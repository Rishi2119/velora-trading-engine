"""
Phase 5 test gate — RiskEngine tests.
Run: python -m pytest tests/test_risk_manager.py -v
"""
import sys
import os
import pytest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.risk.risk_manager import RiskManager, RiskDecision
from backend.app.strategies.strategy_manager import SignalResult
from backend.app.core.config import config


@pytest.fixture
def risk_mgr():
    mgr = RiskManager()
    mgr.reset_daily_if_needed(1000.0)
    return mgr


@pytest.fixture
def mock_signal():
    return SignalResult(
        strategy_name="TestStrat",
        symbol="EURUSD",
        direction="BUY",
        confidence=90.0,
        entry=1.1000,
        sl=1.0950,
        tp=1.1150,  # RR = 3
        reason="Test"
    )


class TestRiskManager:

    def test_approve_valid_signal(self, risk_mgr, mock_signal):
        # 50 pips SL = 500 points
        decision = risk_mgr.validate(
            signal=mock_signal,
            balance=1000.0,
            free_margin=1000.0,
            tick_value=1.0,      # $1 per point for 1 standard lot
            point_size=0.00001,
            contract_size=100000.0
        )
        assert decision.approved is True, decision.reason
        assert decision.normalized_lots > 0

    def test_daily_loss_limit(self, risk_mgr, mock_signal):
        # Config max loss is e.g. 0.05 (5%)
        max_loss = 1000.0 * config.max_daily_loss_pct
        risk_mgr.update_state(-(max_loss + 10.0))
        
        decision = risk_mgr.validate(mock_signal, 1000.0, 1000.0, 1.0, 0.00001, 100000.0)
        assert decision.approved is False
        assert "Daily Loss limit hit" in decision.reason

    def test_max_daily_trades(self, risk_mgr, mock_signal):
        risk_mgr.daily_trades = config.max_trades_per_day
        decision = risk_mgr.validate(mock_signal, 1000.0, 1000.0, 1.0, 0.00001, 100000.0)
        assert decision.approved is False
        assert "Daily Trades limit hit" in decision.reason

    def test_max_positions_limit(self, risk_mgr, mock_signal):
        # Simulate max positions already open
        positions = [{"symbol": f"SYM{i}", "ticket": i} for i in range(config.max_positions)]
        risk_mgr.sync_open_positions(positions)
        
        decision = risk_mgr.validate(mock_signal, 1000.0, 1000.0, 1.0, 0.00001, 100000.0)
        assert decision.approved is False
        assert "Max concurrent positions" in decision.reason

    def test_symbol_exposure_limit(self, risk_mgr, mock_signal):
        # Simulate already having a position in EURUSD
        risk_mgr.sync_open_positions([{"symbol": "EURUSD", "ticket": 123}])
        
        decision = risk_mgr.validate(mock_signal, 1000.0, 1000.0, 1.0, 0.00001, 100000.0)
        assert decision.approved is False
        assert "Already exposed to EURUSD" in decision.reason

    def test_min_rr_rejection(self, risk_mgr, mock_signal):
        # Entry 1.1000, SL 1.0950 (50 pips). Setting TP to 1.1020 (20 pips), RR < 1
        mock_signal.tp = 1.1020
        decision = risk_mgr.validate(mock_signal, 1000.0, 1000.0, 1.0, 0.00001, 100000.0)
        assert decision.approved is False
        assert "R:R too low" in decision.reason

    def test_tight_sl_rejection(self, risk_mgr, mock_signal):
        # SL distance < 5 pips (50 points)
        mock_signal.sl = 1.0998  # 2 pips
        decision = risk_mgr.validate(mock_signal, 1000.0, 1000.0, 1.0, 0.00001, 100000.0)
        assert decision.approved is False
        assert "SL too tight" in decision.reason

    def test_lot_size_calculation(self, risk_mgr, mock_signal):
        balance = 1000.0
        risk_pct = config.risk_per_trade_pct  # usually 0.01 = $10 risk
        # Entry 1.1000, SL 1.0950 -> distance 0.0050 = 500 points
        # 500 points * tick_value (1.0) = $500 loss per 1.0 lot
        # raw lots = $10 / $500 = 0.02 lots
        
        decision = risk_mgr.validate(
            signal=mock_signal,
            balance=balance,
            free_margin=balance,
            tick_value=1.0,
            point_size=0.00001,
            contract_size=100000.0,
            volume_step=0.01
        )
        assert decision.approved is True
        
        expected_risk_usd = balance * risk_pct
        expected_lots = round(expected_risk_usd / 500.0, 2)
        assert decision.normalized_lots == expected_lots

    def test_daily_reset(self, risk_mgr):
        risk_mgr.daily_trades = 5
        risk_mgr.daily_pnl = -50.0
        
        # Simulate next day
        risk_mgr.current_date = date.today() - timedelta(days=1)
        risk_mgr.reset_daily_if_needed(1050.0)
        
        assert risk_mgr.daily_trades == 0
        assert risk_mgr.daily_pnl == 0.0
        assert risk_mgr.session_open_balance == 1050.0
        assert risk_mgr.current_date == date.today()
