"""
Phase 10 test gate — AI Performance Optimizer tests.
Run: python -m pytest tests/test_performance_optimizer.py -v
"""
import sys
import os
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.ai.performance_optimizer import PerformanceOptimizer, calculate_sharpe_ratio
from backend.app.strategies.strategy_manager import EmaRsiStrategy


class TestPerformanceOptimizer:
    
    @pytest.fixture
    def synthetic_trend_data(self):
        """Creates an artificial 400-candle uptrend to yield diverse strategy triggers."""
        dates = pd.date_range("2024-01-01", periods=400, freq="1h")
        base = np.linspace(1.1000, 1.3500, 400)
        
        for i in range(250, 400, 30):
            # Create periodic pullbacks to hit RSI < 40 condition in EmaRsiStrategy
            base[i:i+10] -= 0.0200
            
        df = pd.DataFrame({
            "time": dates,
            "open": base + 0.0005,
            "high": base + 0.0020,
            "low": base - 0.0020,
            "close": base,
            "tick_volume": 1000
        })
        return df

    def test_sharpe_ratio_calculation(self):
        trades = [
            {"pnl": 10.0},
            {"pnl": 10.0},
            {"pnl": -5.0},
            {"pnl": 15.0}
        ]
        sharpe = calculate_sharpe_ratio(trades)
        assert sharpe > 0.0
        
        bad_trades = [
            {"pnl": -10.0},
            {"pnl": -10.0},
            {"pnl": 5.0}
        ]
        bad_sharpe = calculate_sharpe_ratio(bad_trades)
        assert bad_sharpe < 0.0

    def test_grid_search_optimization_loop(self, synthetic_trend_data):
        optimizer = PerformanceOptimizer()
        
        param_grid = {
            "rsi_min": [30, 40],
            "rsi_max": [60],
            "min_rr": [2.0, 3.0]
        }
        
        # Total combinations = 2 * 1 * 2 = 4
        result = optimizer.optimize(
            symbol="EURUSD",
            df=synthetic_trend_data,
            strategy_class=EmaRsiStrategy,
            param_grid=param_grid,
            target_metric="sharpe"
        )
        
        assert "status" in result
        
        if result["status"] == "COMPLETED":
            assert "best_params" in result
            assert "rsi_min" in result["best_params"]
            assert "min_rr" in result["best_params"]
            assert len(result["top_5_results"]) > 0
            assert result["top_5_results"][0]["score"] == result["best_score"]
