"""
Tests for Phase 8 Execution Monitor.
Run: python -m pytest tests/test_execution_monitor.py -v
"""
import sys
import os
import pytest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.execution.execution_monitor import ExecutionMonitor


class TestExecutionMonitor:

    def test_log_successful_trade_slippage(self):
        monitor = ExecutionMonitor()
        
        exec_result = {
            "status": "FILLED",
            "direction": "BUY",
            "symbol": "EURUSD",
            "fill_price": 1.1005
        }
        
        # Expected price was 1.1000, filled at 1.1005 == 5 pips adverse slippage
        monitor.log_execution(expected_price=1.1000, exec_result=exec_result, latency_ms=150.0)
        
        stats = monitor.get_execution_stats()
        assert stats["trades_tracked"] == 1
        assert stats["avg_latency_ms"] == 150.0
        assert stats["avg_slippage"] == pytest.approx(0.0005, 0.00001)

    def test_rejection_tracking(self):
        monitor = ExecutionMonitor()
        
        for _ in range(2):
            monitor.log_execution(
                expected_price=1.10, 
                exec_result={"status": "REJECTED", "reason": "No Money"}, 
                latency_ms=100.0
            )
            
        stats = monitor.get_execution_stats()
        assert stats["trades_tracked"] == 0
        assert stats["rejections_this_hour"] == 2
        
    def test_rejection_reset_on_hour(self):
        monitor = ExecutionMonitor()
        monitor.rejection_count = 5
        # Set last reset to 2 hours ago
        monitor.last_rejection_reset = datetime.now() - timedelta(hours=2)
        
        monitor.log_execution(1.10, {"status": "REJECTED"}, 100.0)
        
        stats = monitor.get_execution_stats()
        # Should reset and then count this 1 rejection
        assert stats["rejections_this_hour"] == 1

    def test_sell_slippage_calculation(self):
        monitor = ExecutionMonitor()
        
        exec_result = {
            "status": "FILLED",
            "direction": "SELL",
            "symbol": "EURUSD",
            "fill_price": 1.0995
        }
        
        # Expected sell 1.1000, filled 1.0995 == 5 pips adverse slippage
        monitor.log_execution(1.1000, exec_result, 100.0)
        
        stats = monitor.get_execution_stats()
        assert stats["avg_slippage"] == pytest.approx(0.0005, 0.00001)
