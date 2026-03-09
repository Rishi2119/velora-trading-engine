"""
Trade Manager Module
Monitors and manages open positions with breakeven, trailing stops, and time-based exits
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from executor import (
    get_open_positions, 
    modify_position, 
    close_trade,
    get_position_profit
)


class TradeManager:
    """
    Manages open trades with advanced position management
    """
    def __init__(self, 
                 breakeven_trigger_pips=10,
                 trailing_start_pips=15,
                 trailing_distance_pips=8,
                 max_trade_duration_hours=24):
        """
        Initialize trade manager
        
        Args:
            breakeven_trigger_pips: Move SL to breakeven after this profit
            trailing_start_pips: Start trailing stop after this profit
            trailing_distance_pips: Distance to keep trailing stop
            max_trade_duration_hours: Auto-close trades older than this
        """
        self.breakeven_trigger = breakeven_trigger_pips
        self.trailing_start = trailing_start_pips
        self.trailing_distance = trailing_distance_pips
        self.max_duration = timedelta(hours=max_trade_duration_hours)
        
        # Track managed trades
        self.managed_trades = {}
    
    def add_trade(self, ticket, direction, entry, sl, tp, symbol="EURUSD"):
        """
        Add a trade to be managed
        
        Args:
            ticket: Position ticket number
            direction: "LONG" or "SHORT"
            entry: Entry price
            sl: Initial stop loss
            tp: Take profit
            symbol: Trading symbol
        """
        self.managed_trades[ticket] = {
            'direction': direction,
            'entry': entry,
            'sl': sl,
            'tp': tp,
            'symbol': symbol,
            'open_time': datetime.now(),
            'breakeven_moved': False,
            'trailing_active': False,
            'highest_profit_pips': 0,
        }
        
        print(f"📊 Managing trade {ticket}: {direction} @ {entry}")
    
    def check_trades(self):
        """
        Check and manage all open trades
        This should be called regularly (every candle or every few seconds)
        """
        positions = get_open_positions()
        
        # Get list of open ticket numbers
        open_tickets = [p.ticket for p in positions]
        
        # Remove closed trades from management
        closed_tickets = [t for t in self.managed_trades.keys() if t not in open_tickets]
        for ticket in closed_tickets:
            print(f"✅ Trade {ticket} closed - removing from management")
            del self.managed_trades[ticket]
        
        # Manage each open position
        for position in positions:
            ticket = position.ticket
            
            # Skip if not being managed
            if ticket not in self.managed_trades:
                continue
            
            # Get trade info
            trade = self.managed_trades[ticket]
            current_price = position.price_current
            
            # Check time-based exit
            if self._check_time_exit(ticket, trade):
                continue
            
            # Check breakeven move
            if not trade['breakeven_moved']:
                self._check_breakeven(ticket, trade, current_price)
            
            # Check trailing stop
            if trade['breakeven_moved'] and not trade['trailing_active']:
                self._check_trailing_start(ticket, trade, current_price)
            
            if trade['trailing_active']:
                self._update_trailing_stop(ticket, trade, current_price)
    
    def _check_time_exit(self, ticket, trade):
        """Close trade if held too long"""
        time_held = datetime.now() - trade['open_time']
        
        if time_held > self.max_duration:
            print(f"⏰ Trade {ticket} held for {time_held} - closing due to time limit")
            close_trade(ticket)
            return True
        
        return False
    
    def _check_breakeven(self, ticket, trade, current_price):
        """Move stop loss to breakeven if profit threshold reached"""
        entry = trade['entry']
        direction = trade['direction']
        symbol = trade['symbol']
        
        # Calculate profit in pips
        if direction == "LONG":
            profit_pips = (current_price - entry) * 10000
        else:  # SHORT
            profit_pips = (entry - current_price) * 10000
        
        # Update highest profit
        if profit_pips > trade['highest_profit_pips']:
            trade['highest_profit_pips'] = profit_pips
        
        # Move to breakeven if threshold reached
        if profit_pips >= self.breakeven_trigger:
            print(f"🎯 Moving {ticket} to breakeven (profit: {profit_pips:.1f} pips)")
            
            # Add small buffer (1 pip) to ensure breakeven
            if direction == "LONG":
                new_sl = entry + (1 / 10000)
            else:
                new_sl = entry - (1 / 10000)
            
            if modify_position(ticket, new_sl=new_sl):
                trade['breakeven_moved'] = True
                trade['sl'] = new_sl
    
    def _check_trailing_start(self, ticket, trade, current_price):
        """Activate trailing stop if profit threshold reached"""
        entry = trade['entry']
        direction = trade['direction']
        
        # Calculate profit in pips
        if direction == "LONG":
            profit_pips = (current_price - entry) * 10000
        else:
            profit_pips = (entry - current_price) * 10000
        
        # Update highest profit
        if profit_pips > trade['highest_profit_pips']:
            trade['highest_profit_pips'] = profit_pips
        
        # Activate trailing if threshold reached
        if profit_pips >= self.trailing_start:
            print(f"🔄 Activating trailing stop for {ticket} (profit: {profit_pips:.1f} pips)")
            trade['trailing_active'] = True
    
    def _update_trailing_stop(self, ticket, trade, current_price):
        """Update trailing stop based on current price"""
        direction = trade['direction']
        current_sl = trade['sl']
        
        # Calculate new trailing stop
        if direction == "LONG":
            new_sl = current_price - (self.trailing_distance / 10000)
            # Only move SL up, never down
            if new_sl > current_sl:
                print(f"📈 Trailing stop up for {ticket}: {current_sl:.5f} → {new_sl:.5f}")
                if modify_position(ticket, new_sl=new_sl):
                    trade['sl'] = new_sl
        
        else:  # SHORT
            new_sl = current_price + (self.trailing_distance / 10000)
            # Only move SL down, never up
            if new_sl < current_sl:
                print(f"📉 Trailing stop down for {ticket}: {current_sl:.5f} → {new_sl:.5f}")
                if modify_position(ticket, new_sl=new_sl):
                    trade['sl'] = new_sl
    
    def get_managed_count(self):
        """Get number of currently managed trades"""
        return len(self.managed_trades)
    
    def close_all_trades(self, reason="Manual close"):
        """Emergency close all managed trades"""
        print(f"🚨 Closing all trades: {reason}")
        
        for ticket in list(self.managed_trades.keys()):
            close_trade(ticket)
            print(f"   Closed {ticket}")
        
        self.managed_trades.clear()
    
    def get_trade_status(self, ticket):
        """Get status information for a specific trade"""
        if ticket not in self.managed_trades:
            return None
        
        trade = self.managed_trades[ticket]
        
        # Get current profit
        profit = get_position_profit(ticket)
        
        return {
            'ticket': ticket,
            'direction': trade['direction'],
            'entry': trade['entry'],
            'current_sl': trade['sl'],
            'tp': trade['tp'],
            'breakeven_moved': trade['breakeven_moved'],
            'trailing_active': trade['trailing_active'],
            'highest_profit_pips': trade['highest_profit_pips'],
            'current_profit': profit,
            'time_held': datetime.now() - trade['open_time'],
        }
    
    def print_summary(self):
        """Print summary of all managed trades"""
        if not self.managed_trades:
            print("📊 No trades currently managed")
            return
        
        print(f"\n📊 Trade Manager Summary ({len(self.managed_trades)} trades)")
        print("-" * 80)
        
        for ticket, trade in self.managed_trades.items():
            status = self.get_trade_status(ticket)
            print(f"Ticket: {ticket} | {trade['direction']}")
            print(f"  Entry: {trade['entry']:.5f} | SL: {status['current_sl']:.5f} | TP: {trade['tp']:.5f}")
            print(f"  Breakeven: {'YES' if status['breakeven_moved'] else 'NO'} | "
                  f"Trailing: {'YES' if status['trailing_active'] else 'NO'}")
            print(f"  Max Profit: {status['highest_profit_pips']:.1f} pips | "
                  f"Current: ${status['current_profit']:.2f}")
            print(f"  Time Held: {status['time_held']}")
            print()
