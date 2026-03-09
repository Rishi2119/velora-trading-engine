"""
Performance Tracker
Track trading performance and statistics
"""

import json
import os
from datetime import date
from pathlib import Path


class PerformanceTracker:
    """Track performance metrics"""
    
    def __init__(self, filepath="logs/performance.json"):
        self.filepath = filepath
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        self.stats = self.load_stats()
    
    def load_stats(self):
        """Load stats from file"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0,
            'daily': {}
        }
    
    def save_stats(self):
        """Save stats to file"""
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving stats: {e}")
    
    def get_daily_stats(self):
        """Get today's stats"""
        today = str(date.today())
        
        if today not in self.stats['daily']:
            self.stats['daily'][today] = {
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'pnl': 0.0
            }
        
        return self.stats['daily'][today]
    
    def record_trade(self, pnl):
        """Record a completed trade"""
        self.stats['total_trades'] += 1
        self.stats['total_pnl'] += pnl
        
        daily = self.get_daily_stats()
        daily['trades'] += 1
        daily['pnl'] += pnl
        
        if pnl > 0:
            self.stats['wins'] += 1
            daily['wins'] += 1
        elif pnl < 0:
            self.stats['losses'] += 1
            daily['losses'] += 1
        
        self.save_stats()
    
    def is_daily_loss_limit_hit(self, max_loss):
        """Check if daily loss limit hit"""
        daily = self.get_daily_stats()
        return daily['pnl'] <= -max_loss
    
    def get_win_rate(self):
        """Calculate win rate"""
        total = self.stats['wins'] + self.stats['losses']
        if total == 0:
            return 0
        return (self.stats['wins'] / total) * 100
    
    def reset_daily(self):
        """Reset daily stats"""
        pass  # Daily stats created on demand
    
    def print_summary(self):
        """Print performance summary"""
        print("\n" + "="*80)
        print("📊 PERFORMANCE SUMMARY")
        print("="*80)
        
        print(f"\nTotal Trades: {self.stats['total_trades']}")
        print(f"Wins: {self.stats['wins']} | Losses: {self.stats['losses']}")
        print(f"Win Rate: {self.get_win_rate():.1f}%")
        print(f"Total PnL: ${self.stats['total_pnl']:.2f}")
        
        daily = self.get_daily_stats()
        print(f"\nToday's Stats:")
        print(f"  Trades: {daily['trades']}")
        print(f"  PnL: ${daily['pnl']:.2f}")
        
        print("="*80 + "\n")
