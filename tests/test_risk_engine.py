import pytest
import sys
import os

# Add root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from risk import RiskManager

def test_position_sizing():
    rm = RiskManager()
    # Mock account info: 10000 Balance, 10000 Equity
    free_margin = 10000.0
    risk_pct = 0.01 # 1%
    
    # EURUSD trade: Entry 1.1000, SL 1.0950 (50 pips)
    # Risk = 100 USD
    # Risk per pip = 100 / 50 = 2 USD
    # In MT5, 1 lot of EURUSD = 100,000 units. 1 pip (0.0001) = 10 USD.
    # So 2 USD/pip = 0.2 lots.
    
    lots = rm.calculate_position_size(
        symbol="EURUSD",
        entry=1.1000,
        sl=1.0950,
        free_margin=free_margin,
        risk_pct=risk_pct
    )
    
    assert lots > 0
    print(f"\n[PASS] Position Sizing: {lots} lots for 1% risk on $10k with 50 pip SL")

def test_daily_loss_limit():
    rm = RiskManager(max_daily_loss=0.05)
    rm.set_session_open_balance(10000.0)
    
    # Simulate realized loss
    with rm._lock:
        rm._daily_pnl = -600.0 # 6% loss
    
    allowed, reason = rm.can_trade()
    assert allowed == False
    assert "Daily loss limit reached" in reason
    print(f"[PASS] Trade blocked by daily loss limit: {reason}")

if __name__ == "__main__":
    test_position_sizing()
    test_daily_loss_limit()
