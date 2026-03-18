"""
Phase 6 test gate — Execution Engine tests.
Run: python -m pytest tests/test_executor_validation.py -v
"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.execution.trade_executor import TradeExecutor
from backend.app.strategies.strategy_manager import SignalResult
from backend.app.risk.risk_manager import RiskDecision
from backend.app.core.config import config


@pytest.fixture
def mock_signal():
    return SignalResult(
        strategy_name="TestStrat",
        symbol="EURUSD",
        direction="BUY",
        confidence=90.0,
        entry=1.1000,
        sl=1.0950,
        tp=1.1150,
        reason="Test"
    )

@pytest.fixture
def mock_decision():
    return RiskDecision(
        approved=True,
        reason="OK",
        normalized_lots=0.1,
        effective_risk_pct=0.01,
        pip_value_usd=10.0
    )


class TestTradeExecutor:
    
    def test_paper_mode_execution(self, mock_signal, mock_decision):
        config.engine_mode = "paper"
        executor = TradeExecutor()
        
        result = executor.execute_trade(mock_signal, mock_decision)
        
        assert result["status"] == "FILLED"
        assert result["type"] == "PAPER"
        assert result["volume"] == 0.1
        assert "ticket" in result
        
    @patch('backend.app.execution.trade_executor.mt5_conn')
    @patch('backend.app.execution.trade_executor.MT5_AVAILABLE', True)
    def test_live_mode_rejects_wide_spread(self, mock_mt5_conn, mock_signal, mock_decision):
        config.engine_mode = "live"
        config.max_spread_pips = 2  # 20 points
        
        # Mock connection and symbol info returning wide spread
        mock_mt5_conn.is_connected = True
        mock_mt5_conn.get_symbol_info.return_value = {"spread": 25, "filling_mode": 0}
        
        executor = TradeExecutor()
        result = executor.execute_trade(mock_signal, mock_decision)
        
        assert result["status"] == "REJECTED"
        assert "Spread too wide" in result["reason"]
        
    @patch('backend.app.execution.trade_executor.mt5_conn')
    def test_live_mode_order_send_success(self, mock_mt5_conn, mock_signal, mock_decision):
        config.engine_mode = "live"
        config.max_spread_pips = 3
        
        # We also need to patch MT5_AVAILABLE correctly for the test
        with patch('backend.app.execution.trade_executor.MT5_AVAILABLE', True):
            # Also patch mt5 module in trade_executor to a MagicMock to prevent NameError
            # if the real MT5 isn't installed.
            mock_mt5 = MagicMock()
            mock_mt5.TRADE_RETCODE_DONE = 10009
            mock_mt5.ORDER_TYPE_BUY = 0
            mock_mt5.ORDER_TYPE_SELL = 1
            mock_mt5.TRADE_ACTION_DEAL = 1
            mock_mt5.ORDER_TIME_GTC = 0
            
            with patch('backend.app.execution.trade_executor.mt5', mock_mt5):
                mock_mt5_conn.is_connected = True
                mock_mt5_conn.get_symbol_info.return_value = {"spread": 10, "filling_mode": 1} # 1 = FOK
                
                # Mock successful order_send
                mock_result = MagicMock()
                mock_result.retcode = 10009 # TRADE_RETCODE_DONE
                mock_result.order = 12345
                mock_result.volume = 0.1
                mock_result.price = 1.1001
                mock_result.deal = 54321
                
                mock_mt5_conn.order_send.return_value = mock_result
                
                executor = TradeExecutor()
                result = executor.execute_trade(mock_signal, mock_decision)
                
                assert result["status"] == "FILLED"
                assert result["type"] == "LIVE"
                assert result["ticket"] == 12345
                assert result["deal_id"] == 54321
                
        # Reset
        config.engine_mode = "paper"
