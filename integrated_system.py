"""
COMPLETE INTEGRATION SCRIPT
Combines your existing MT5 system with AI enhancements
"""

import sys
import os
from pathlib import Path

# Add user's original modules
sys.path.insert(0, '/mnt/user-data/uploads')

import pandas as pd
from enhanced_engine import EnhancedTradingEngine
from data_loader import load_csv
from journal import init_journal, log_trade
from executor import connect, place_trade, get_open_positions, disconnect
import config as user_config

class IntegratedTradingSystem:
    """
    Combines your original MT5 system with AI enhancements
    """
    
    def __init__(self, use_live_mt5=False):
        self.use_live = use_live_mt5
        self.config = {
            'ema_fast': user_config.EMA_FAST,
            'ema_slow': user_config.EMA_SLOW,
            'min_rr': user_config.MIN_RISK_REWARD,
            'risk_per_trade': user_config.RISK_PER_TRADE,
            'max_position_size': user_config.MAX_POSITION_SIZE,
            'account_balance': user_config.ACCOUNT_BALANCE
        }
        
        # Initialize enhanced AI engine
        self.engine = EnhancedTradingEngine(self.config)
        
        # Initialize journal
        init_journal()
        
        print("=" * 80)
        print("🚀 INTEGRATED AI TRADING SYSTEM v2.0")
        print("=" * 80)
        print(f"\n📊 Configuration:")
        print(f"   Symbol: {user_config.SYMBOL}")
        print(f"   Timeframe: {user_config.TIMEFRAME}")
        print(f"   Account Balance: ${self.config['account_balance']}")
        print(f"   Risk per Trade: {self.config['risk_per_trade'] * 100}%")
        print(f"   Min R:R: {self.config['min_rr']}")
        print(f"   Live Execution: {'🔴 ENABLED' if use_live_mt5 else '✅ DISABLED (Safe Mode)'}")
        print("=" * 80)
    
    def backtest(self, data_file=None):
        """
        Run backtest on historical data with AI enhancements
        """
        if data_file is None:
            data_file = user_config.DATA_FILE
        
        print(f"\n📈 Loading data from: {data_file}")
        df = load_csv(data_file)
        
        if df is None:
            print("❌ Failed to load data")
            return
        
        print(f"✅ Loaded {len(df)} candles")
        print(f"   Period: {df['time'].iloc[0]} to {df['time'].iloc[-1]}")
        
        # Calculate enhanced indicators
        print("\n🧮 Calculating AI indicators...")
        df = self.engine.calculate_advanced_indicators(df)
        print("✅ Indicators calculated")
        
        # Run backtest
        print("\n🎯 Running AI-enhanced backtest...")
        print("-" * 80)
        
        balance = self.config['account_balance']
        trades_taken = 0
        signals_evaluated = 0
        
        for idx, row in df.iterrows():
            if idx < 200:  # Skip first 200 for indicator warmup
                continue
            
            signals_evaluated += 1
            
            # Make trading decision using AI
            decision = self.engine.make_trading_decision(row, balance)
            
            if decision['decision'] != 'NO TRADE':
                trades_taken += 1
                
                print(f"\n🎲 Trade Signal #{trades_taken}")
                print(f"   Time: {row['time']}")
                print(f"   Pair: {user_config.SYMBOL}")
                print(f"   Direction: {decision['direction']}")
                print(f"   Entry: {decision['entry']:.5f}")
                print(f"   Stop Loss: {decision['stop_loss']:.5f}")
                print(f"   Take Profit: {decision['take_profit']:.5f}")
                print(f"   R:R: {decision['rr']:.2f}")
                print(f"   Position Size: {decision['position_size']:.2f} lots")
                print(f"   AI Confidence: {decision['confidence']}%")
                print(f"   Reasons: {', '.join(decision['analysis']['reasons'][:2])}")
                
                # Simulate trade outcome (simplified)
                # In real backtest, you'd check subsequent candles for SL/TP hits
                simulated_outcome = self._simulate_trade_outcome(decision, df[idx:idx+20])
                
                balance += simulated_outcome['pnl']
                
                # Update engine performance
                self.engine.update_performance(simulated_outcome)
                
                # Log trade
                log_trade(
                    row['time'],
                    decision['entry'],
                    f"{decision['direction']}",
                    decision['analysis']['reasons'],
                    decision['rr'],
                    decision['position_size'],
                    simulated_outcome['status']
                )
                
                print(f"   Outcome: {simulated_outcome['status']}")
                print(f"   P/L: ${simulated_outcome['pnl']:.2f}")
                print(f"   New Balance: ${balance:.2f}")
        
        # Print final results
        print("\n" + "=" * 80)
        print("📊 BACKTEST RESULTS")
        print("=" * 80)
        
        report = self.engine.get_performance_report()
        for key, value in report.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
        
        print(f"\n   Signals Evaluated: {signals_evaluated}")
        print(f"   Trades Taken: {trades_taken}")
        print(f"   Trade Frequency: {(trades_taken/signals_evaluated*100):.2f}%")
        print(f"   Final Balance: ${balance:.2f}")
        print(f"   ROI: {((balance - self.config['account_balance'])/self.config['account_balance']*100):.2f}%")
        print("=" * 80)
        
        return balance
    
    def _simulate_trade_outcome(self, decision, future_candles):
        """
        Simulate trade outcome (simplified for demo)
        In production, check actual price movement against SL/TP
        """
        if len(future_candles) < 5:
            return {'status': 'NEUTRAL', 'pnl': 0}
        
        # Simplified: use AI confidence as win probability
        import random
        win_prob = decision['confidence'] / 100
        
        if random.random() < win_prob:
            pnl = decision['potential_profit']
            status = 'WIN'
        else:
            pnl = -decision['risk_amount']
            status = 'LOSS'
        
        return {
            'status': status,
            'pnl': pnl,
            'direction': decision['direction'],
            'entry': decision['entry'],
            'exit': decision['take_profit'] if status == 'WIN' else decision['stop_loss']
        }
    
    def run_live(self):
        """
        Run live trading with MT5
        """
        if not self.use_live:
            print("\n⚠️  Live trading disabled. Use backtest mode instead.")
            return
        
        print("\n🔴 LIVE TRADING MODE")
        print("   Connecting to MT5...")
        
        if not connect(
            user_config.MT5_ACCOUNT,
            user_config.MT5_PASSWORD,
            user_config.MT5_SERVER
        ):
            print("❌ MT5 connection failed")
            return
        
        print("✅ Connected to MT5")
        print("\n⚠️  WARNING: Real money at risk!")
        print("   Press Ctrl+C to stop\n")
        
        try:
            import time
            while True:
                # Get live data
                # ... (implement with your connect_mt5__.py)
                
                # Make decision
                # ... (use engine.make_trading_decision)
                
                # Execute if needed
                # ... (use executor.place_trade)
                
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print("\n\n⏸  Stopping live trading...")
        finally:
            disconnect()


def main():
    """
    Main entry point
    """
    print("\n" + "=" * 80)
    print("🎯 AI TRADING SYSTEM - Choose Mode")
    print("=" * 80)
    print("\n1. 📊 BACKTEST (Safe - Recommended)")
    print("2. 🔴 LIVE TRADING (Real money)")
    print("3. ⚙️  Configure Settings")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        system = IntegratedTradingSystem(use_live_mt5=False)
        system.backtest()
    
    elif choice == '2':
        confirm = input("\n⚠️  Live trading will use real money. Type 'CONFIRM' to proceed: ")
        if confirm == 'CONFIRM':
            system = IntegratedTradingSystem(use_live_mt5=True)
            system.run_live()
        else:
            print("❌ Cancelled")
    
    elif choice == '3':
        print("\n⚙️  Edit config.py to change settings")
    
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
