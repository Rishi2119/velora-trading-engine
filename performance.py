"""
Performance Tracker Module
Tracks trading performance, statistics, and generates reports
"""

import json
import os
from datetime import datetime, date
from pathlib import Path


class PerformanceTracker:
    """
    Track and analyze trading performance
    """
    def __init__(self, filepath="logs/performance.json"):
        """
        Initialize performance tracker
        
        Args:
            filepath: Path to save performance data
        """
        self.filepath = filepath
        self.ensure_directory()
        self.stats = self.load_stats()
        self.current_date = date.today()
    
    def ensure_directory(self):
        """Create logs directory if it doesn't exist"""
        Path(self.filepath).parent.mkdir(parents=True, exist_ok=True)
    
    def load_stats(self):
        """Load performance statistics from file"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading performance stats: {e}")
        
        # Return default stats structure
        return {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'breakeven': 0,
            'total_pnl': 0.0,
            'gross_profit': 0.0,
            'gross_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'current_streak': 0,
            'streak_type': None,  # 'win' or 'loss'
            'daily': {},  # Daily stats by date
            'trades': [],  # Individual trade records
            'equity_curve': [],  # Running equity
        }
    
    def save_stats(self):
        """Save performance statistics to file"""
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving performance stats: {e}")
    
    def check_new_day(self):
        """Check if it's a new trading day and reset daily stats if needed"""
        today = date.today()
        if today != self.current_date:
            print(f"📅 New trading day: {today}")
            self.current_date = today
            return True
        return False
    
    def get_daily_stats(self):
        """Get statistics for current day"""
        today_str = str(date.today())
        
        if today_str not in self.stats['daily']:
            self.stats['daily'][today_str] = {
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'pnl': 0.0,
                'max_drawdown': 0.0,
            }
        
        return self.stats['daily'][today_str]
    
    def record_trade(self, pnl, direction, entry, exit_price, duration_minutes=0, setup=""):
        """
        Record a completed trade
        
        Args:
            pnl: Profit/loss in account currency
            direction: "LONG" or "SHORT"
            entry: Entry price
            exit_price: Exit price
            duration_minutes: How long trade was held
            setup: Trade setup description
        """
        # Determine win/loss/breakeven
        if pnl > 0:
            outcome = 'WIN'
            self.stats['wins'] += 1
            self.stats['gross_profit'] += pnl
            
            if pnl > self.stats['largest_win']:
                self.stats['largest_win'] = pnl
            
            # Update streak
            if self.stats['streak_type'] == 'win':
                self.stats['current_streak'] += 1
            else:
                self.stats['current_streak'] = 1
                self.stats['streak_type'] = 'win'
            
            if self.stats['current_streak'] > self.stats['max_consecutive_wins']:
                self.stats['max_consecutive_wins'] = self.stats['current_streak']
        
        elif pnl < 0:
            outcome = 'LOSS'
            self.stats['losses'] += 1
            self.stats['gross_loss'] += abs(pnl)
            
            if pnl < self.stats['largest_loss']:
                self.stats['largest_loss'] = pnl
            
            # Update streak
            if self.stats['streak_type'] == 'loss':
                self.stats['current_streak'] += 1
            else:
                self.stats['current_streak'] = 1
                self.stats['streak_type'] = 'loss'
            
            if self.stats['current_streak'] > self.stats['max_consecutive_losses']:
                self.stats['max_consecutive_losses'] = self.stats['current_streak']
        
        else:
            outcome = 'BREAKEVEN'
            self.stats['breakeven'] += 1
            self.stats['current_streak'] = 0
            self.stats['streak_type'] = None
        
        # Update totals
        self.stats['total_trades'] += 1
        self.stats['total_pnl'] += pnl
        
        # Add to equity curve
        self.stats['equity_curve'].append({
            'trade_number': self.stats['total_trades'],
            'pnl': pnl,
            'cumulative_pnl': self.stats['total_pnl'],
            'timestamp': str(datetime.now())
        })
        
        # Update daily stats
        daily = self.get_daily_stats()
        daily['trades'] += 1
        daily['pnl'] += pnl
        
        if pnl > 0:
            daily['wins'] += 1
        elif pnl < 0:
            daily['losses'] += 1
        
        # Track max drawdown for the day
        if daily['pnl'] < daily['max_drawdown']:
            daily['max_drawdown'] = daily['pnl']
        
        # Record individual trade
        trade_record = {
            'timestamp': str(datetime.now()),
            'direction': direction,
            'entry': entry,
            'exit': exit_price,
            'pnl': pnl,
            'outcome': outcome,
            'duration_minutes': duration_minutes,
            'setup': setup,
        }
        
        self.stats['trades'].append(trade_record)
        
        # Save to file
        self.save_stats()
        
        print(f"📝 Trade recorded: {outcome} | PnL: ${pnl:.2f}")
        
        return outcome
    
    def is_daily_loss_limit_hit(self, max_daily_loss):
        """
        Check if daily loss limit has been hit
        
        Args:
            max_daily_loss: Maximum allowed daily loss
        
        Returns:
            True if limit hit, False otherwise
        """
        daily = self.get_daily_stats()
        return daily['pnl'] <= -max_daily_loss
    
    def get_win_rate(self):
        """Calculate overall win rate percentage"""
        total = self.stats['wins'] + self.stats['losses']
        if total == 0:
            return 0.0
        return (self.stats['wins'] / total) * 100
    
    def get_profit_factor(self):
        """Calculate profit factor (gross profit / gross loss)"""
        if self.stats['gross_loss'] == 0:
            return float('inf') if self.stats['gross_profit'] > 0 else 0.0
        return self.stats['gross_profit'] / self.stats['gross_loss']
    
    def get_average_win(self):
        """Calculate average winning trade"""
        if self.stats['wins'] == 0:
            return 0.0
        return self.stats['gross_profit'] / self.stats['wins']
    
    def get_average_loss(self):
        """Calculate average losing trade"""
        if self.stats['losses'] == 0:
            return 0.0
        return self.stats['gross_loss'] / self.stats['losses']
    
    def get_expectancy(self):
        """Calculate trade expectancy"""
        total = self.stats['wins'] + self.stats['losses']
        if total == 0:
            return 0.0
        
        win_rate = self.stats['wins'] / total
        avg_win = self.get_average_win()
        avg_loss = self.get_average_loss()
        
        return (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
    
    def print_summary(self):
        """Print performance summary"""
        print("\n" + "="*80)
        print("📊 PERFORMANCE SUMMARY")
        print("="*80)
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Trades: {self.stats['total_trades']}")
        print(f"   Wins: {self.stats['wins']} | Losses: {self.stats['losses']} | Breakeven: {self.stats['breakeven']}")
        print(f"   Win Rate: {self.get_win_rate():.2f}%")
        print(f"   Total PnL: ${self.stats['total_pnl']:.2f}")
        
        print(f"\n💰 Financial Metrics:")
        print(f"   Gross Profit: ${self.stats['gross_profit']:.2f}")
        print(f"   Gross Loss: ${self.stats['gross_loss']:.2f}")
        print(f"   Profit Factor: {self.get_profit_factor():.2f}")
        print(f"   Average Win: ${self.get_average_win():.2f}")
        print(f"   Average Loss: ${self.get_average_loss():.2f}")
        print(f"   Expectancy: ${self.get_expectancy():.2f}")
        
        print(f"\n🎯 Best/Worst:")
        print(f"   Largest Win: ${self.stats['largest_win']:.2f}")
        print(f"   Largest Loss: ${self.stats['largest_loss']:.2f}")
        print(f"   Max Consecutive Wins: {self.stats['max_consecutive_wins']}")
        print(f"   Max Consecutive Losses: {self.stats['max_consecutive_losses']}")
        
        # Daily stats
        daily = self.get_daily_stats()
        print(f"\n📅 Today's Performance:")
        print(f"   Trades: {daily['trades']}")
        print(f"   Wins: {daily['wins']} | Losses: {daily['losses']}")
        print(f"   PnL: ${daily['pnl']:.2f}")
        print(f"   Max Drawdown: ${daily['max_drawdown']:.2f}")
        
        print("="*80 + "\n")
    
    def print_recent_trades(self, count=10):
        """Print recent trades"""
        print(f"\n📋 Last {count} Trades:")
        print("-" * 80)
        
        recent = self.stats['trades'][-count:]
        
        for i, trade in enumerate(recent, 1):
            print(f"{i}. {trade['timestamp']} | {trade['direction']} | {trade['outcome']}")
            print(f"   Entry: {trade['entry']:.5f} → Exit: {trade['exit']:.5f}")
            print(f"   PnL: ${trade['pnl']:.2f} | Duration: {trade['duration_minutes']} min")
            print()
    
    def reset_daily(self):
        """Reset daily statistics (called at start of new day)"""
        today_str = str(date.today())
        
        if today_str in self.stats['daily']:
            print(f"📊 Yesterday's final stats: {self.stats['daily'][today_str]}")
        
        # Daily stats are created on demand, so nothing to reset
        print("✅ Daily stats reset for new trading day")
    
    def export_to_csv(self, filepath="logs/trades_export.csv"):
        """Export all trades to CSV file"""
        import csv
        
        try:
            with open(filepath, 'w', newline='') as f:
                if not self.stats['trades']:
                    print("No trades to export")
                    return
                
                fieldnames = self.stats['trades'][0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(self.stats['trades'])
            
            print(f"✅ Trades exported to {filepath}")
        
        except Exception as e:
            print(f"❌ Error exporting trades: {e}")
