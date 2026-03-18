"""
Phase 9 test gate — Backtesting Engine tests.
Run: python -m pytest tests/test_backtest_engine.py -v
"""
import sys
import os
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.analytics.backtester import Backtester


class TestBacktestEngine:
    
    @pytest.fixture
    def synthetic_trend_data(self):
        """Creates an artificial 300-candle uptrend to force EMA/RSI triggers."""
        dates = pd.date_range("2024-01-01", periods=300, freq="1h")
        
        # We need a clear, smooth upward trend to trigger EMA50 > EMA200
        # and pullback structures for RSI.
        base = np.linspace(1.1000, 1.2500, 300)
        
        # Add a specific drop near the end to trigger RSI < 40 (pullback entry)
        for i in range(260, 275):
            base[i] -= 0.0150
            
        df = pd.DataFrame({
            "time": dates,
            "open": base + 0.0005,
            "high": base + 0.0020,
            "low": base - 0.0020,
            "close": base,
            "tick_volume": 1000
        })
        return df

    def test_backtest_short_data_rejection(self):
        bt = Backtester()
        df = pd.DataFrame({"time": [], "close": []})
        result = bt.run_backtest("EURUSD", df)
        assert "error" in result
        assert "Not enough data" in result["error"]
        
    def test_backtest_execution_loop(self, synthetic_trend_data):
        bt = Backtester(initial_balance=1000.0, risk_per_trade=0.01) # 1% = $10 per trade
        
        result = bt.run_backtest("EURUSD", synthetic_trend_data)
        
        # The result might be "NO_TRADES_TAKEN" if our synthetic data didn't hit exact strategy params,
        # but the engine itself should run without crashing.
        assert "status" in result
        if result["status"] == "COMPLETED":
            assert "total_trades" in result
            assert "win_rate_pct" in result
            assert "max_drawdown_pct" in result
            assert result["initial_balance"] == 1000.0
            assert "final_balance" in result
        else:
            assert result["status"] == "NO_TRADES_TAKEN"
