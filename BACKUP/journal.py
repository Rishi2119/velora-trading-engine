"""
Trade Journal
Log all trade decisions
"""

import csv
import os
from datetime import datetime
from pathlib import Path


def init_journal(filepath="logs/trade_journal.csv"):
    """Initialize trade journal CSV file"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    if not os.path.exists(filepath):
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp',
                'candle_time',
                'price',
                'decision',
                'reasons',
                'rr',
                'position_size',
                'status'
            ])
        print(f"✅ Trade journal created: {filepath}")


def log_trade(candle_time, price, decision, reasons, rr, position_size, status, 
              filepath="logs/trade_journal.csv"):
    """
    Log a trade decision
    
    Args:
        candle_time: Time of the candle
        price: Current price
        decision: Trade decision (e.g., "TRADE LONG", "NO TRADE")
        reasons: List of reasons
        rr: Risk-reward ratio
        position_size: Position size in lots
        status: Trade status
    """
    try:
        with open(filepath, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                candle_time,
                price,
                decision,
                ' | '.join(reasons) if isinstance(reasons, list) else reasons,
                rr,
                position_size,
                status
            ])
    except Exception as e:
        print(f"⚠️ Error logging trade: {e}")
