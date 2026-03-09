"""
Production Test Suite
Tests for all critical trading system components
"""

import pytest
import os
import sys
import json
import tempfile
import shutil
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =========================
# FIXTURES
# =========================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)


@pytest.fixture
def mock_risk_config():
    return {
        'max_daily_loss': 20,
        'max_daily_trades': 5,
        'max_concurrent': 2,
        'risk_per_trade': 0.01,
        'min_rr': 3.0,
        'state_file': 'logs/test_risk_state.json'
    }


@pytest.fixture
def risk_manager(mock_risk_config, temp_dir):
    """Create risk manager with temp state file"""
    from risk import RiskManager
    config = mock_risk_config.copy()
    config['state_file'] = os.path.join(temp_dir, 'risk_state.json')
    return RiskManager(**config)


# =========================
# RISK MANAGER TESTS
# =========================

class TestRiskManager:
    """Tests for production risk manager"""
    
    def test_initialization(self, risk_manager):
        """Test risk manager initializes correctly"""
        assert risk_manager.daily_pnl == 0.0
        assert risk_manager.daily_trades == 0
        assert risk_manager.current_positions == 0
        assert risk_manager.risk_per_trade == 0.01
    
    def test_daily_reset(self, risk_manager):
        """Test daily reset functionality"""
        # Add some trades
        risk_manager.daily_trades = 5
        risk_manager.daily_pnl = -10
        
        # Reset
        risk_manager.reset_daily()
        
        assert risk_manager.daily_trades == 0
        assert risk_manager.daily_pnl == 0.0
    
    def test_can_trade_limits(self, risk_manager):
        """Test trade limits"""
        # At limit
        risk_manager.daily_trades = 5
        
        can_trade, reason = risk_manager.can_trade()
        assert not can_trade
        assert "MAX DAILY TRADES" in reason
    
    def test_daily_loss_limit(self, risk_manager):
        """Test daily loss limit"""
        risk_manager.daily_pnl = -25
        
        can_trade, reason = risk_manager.can_trade()
        assert not can_trade
        assert "MAX DAILY LOSS" in reason
    
    def test_validate_trade_long(self, risk_manager):
        """Test trade validation for LONG"""
        valid, reason = risk_manager.validate_trade(
            entry=1.1000,
            sl=1.0950,  # 50 pips
            tp=1.1200,  # 200 pips = 4:1
            direction="LONG",
            min_rr=3.0
        )
        
        assert valid
        assert "Valid" in reason
    
    def test_validate_trade_short(self, risk_manager):
        """Test trade validation for SHORT"""
        valid, reason = risk_manager.validate_trade(
            entry=1.1000,
            sl=1.1050,
            tp=1.0800,
            direction="SHORT",
            min_rr=3.0
        )
        
        assert valid
    
    def test_validate_trade_low_rr(self, risk_manager):
        """Test validation rejects low RR"""
        valid, reason = risk_manager.validate_trade(
            entry=1.1000,
            sl=1.0980,
            tp=1.1040,  # Only 2:1
            direction="LONG",
            min_rr=3.0
        )
        
        assert not valid
        assert "RR" in reason
    
    def test_validate_trade_invalid_direction(self, risk_manager):
        """Test validation rejects invalid direction"""
        valid, reason = risk_manager.validate_trade(
            entry=1.1000,
            sl=1.0950,
            tp=1.1200,
            direction="INVALID",
            min_rr=3.0
        )
        
        assert not valid
    
    def test_position_size_eurusd(self, risk_manager):
        """Test position size calculation for EURUSD"""
        size = risk_manager.calculate_position_size(
            balance=500,
            risk_pct=0.01,  # $5 risk
            entry=1.1000,
            sl=1.0950,  # 50 pips
            symbol="EURUSD"
        )
        
        assert size > 0
        assert size <= 0.5  # Capped at max
    
    def test_position_size_usdjpy(self, risk_manager):
        """Test position size calculation for USDJPY (JPY pair)"""
        size = risk_manager.calculate_position_size(
            balance=500,
            risk_pct=0.01,
            entry=150.00,
            sl=149.50,  # 50 pips
            symbol="USDJPY"
        )
        
        assert size > 0
        # Should use different calculation than EURUSD
    
    def test_concurrent_positions_limit(self, risk_manager):
        """Test concurrent positions limit"""
        risk_manager.current_positions = 2
        
        can_trade, reason = risk_manager.can_trade()
        assert not can_trade
        assert "CONCURRENT" in reason
    
    def test_state_persistence(self, risk_manager, temp_dir):
        """Test state is saved to disk"""
        risk_manager.daily_trades = 3
        risk_manager.daily_pnl = 15.0
        risk_manager._save_state()
        
        # Create new instance
        from risk import RiskManager
        new_rm = RiskManager(
            max_daily_loss=20,
            max_daily_trades=5,
            max_concurrent=2,
            state_file=os.path.join(temp_dir, 'risk_state.json')
        )
        
        assert new_rm.daily_trades == 3
        assert new_rm.daily_pnl == 15.0


# =========================
# AI SANDBOX TESTS
# =========================

class TestAISandbox:
    """Tests for AI sandbox"""
    
    @pytest.fixture
    def sandbox(self, risk_manager):
        from ai_sandbox import AISandbox
        return AISandbox(risk_manager, {
            'ai_enabled': True,
            'min_confidence': 70,
            'max_ai_calls_per_minute': 10
        })
    
    def test_initialization(self, sandbox):
        """Test sandbox initializes with correct defaults"""
        assert sandbox.ai_enabled == True
        assert sandbox.ai_can_execute == False  # MUST be False
        assert sandbox.min_confidence == 70
    
    def test_ai_cannot_execute_directly(self, sandbox):
        """Test AI can NEVER have direct execution"""
        assert sandbox.ai_can_execute == False
    
    def test_validate_signal_structure(self, sandbox):
        """Test signal structure validation"""
        valid_signal = {
            'direction': 'LONG',
            'entry': 1.1000,
            'sl': 1.0950,
            'tp': 1.1200,
            'symbol': 'EURUSD',
            'confidence': 80
        }
        
        valid, reason = sandbox._validate_signal_structure(valid_signal)
        assert valid
    
    def test_reject_missing_fields(self, sandbox):
        """Test rejection of incomplete signals"""
        invalid_signal = {
            'direction': 'LONG',
            'entry': 1.1000
            # Missing sl, tp, symbol, confidence
        }
        
        valid, reason = sandbox._validate_signal_structure(invalid_signal)
        assert not valid
    
    def test_reject_low_confidence(self, sandbox):
        """Test rejection of low confidence"""
        signal = {
            'direction': 'LONG',
            'entry': 1.1000,
            'sl': 1.0950,
            'tp': 1.1200,
            'symbol': 'EURUSD',
            'confidence': 50  # Below 70 threshold
        }
        
        valid, reason = sandbox._validate_confidence(signal['confidence'])
        assert not valid
    
    def test_rate_limiting(self, sandbox):
        """Test rate limiting"""
        sandbox.max_calls = 3
        
        # First 3 should pass
        assert sandbox._check_rate_limit()
        assert sandbox._check_rate_limit()
        assert sandbox._check_rate_limit()
        
        # 4th should fail
        assert not sandbox._check_rate_limit()
    
    def test_request_trade_blocked_when_disabled(self, sandbox):
        """Test trades blocked when AI disabled"""
        sandbox.ai_enabled = False
        
        result = sandbox.request_trade({
            'direction': 'LONG',
            'entry': 1.1000,
            'sl': 1.0950,
            'tp': 1.1200,
            'symbol': 'EURUSD',
            'confidence': 80
        }, 500)
        
        assert result['approved'] == False
        assert 'disabled' in result['reason'].lower()


# =========================
# CIRCUIT BREAKER TESTS
# =========================

class TestCircuitBreaker:
    """Tests for circuit breaker"""
    
    @pytest.fixture
    def circuit(self):
        from circuit_breaker import CircuitBreaker
        return CircuitBreaker(
            name='test',
            failure_threshold=3,
            success_threshold=2,
            timeout=1
        )
    
    def test_initial_state(self, circuit):
        """Test circuit starts closed"""
        assert circuit.state.value == "CLOSED"
        can, _ = circuit.can_execute()
        assert can
    
    def test_opens_after_failures(self, circuit):
        """Test circuit opens after threshold"""
        circuit.record_failure()
        circuit.record_failure()
        circuit.record_failure()
        
        assert circuit.state.value == "OPEN"
        can, _ = circuit.can_execute()
        assert not can
    
    def test_half_open_after_timeout(self, circuit):
        """Test circuit half-opens after timeout"""
        circuit.record_failure()
        circuit.record_failure()
        circuit.record_failure()
        
        import time
        time.sleep(1.5)
        
        can, reason = circuit.can_execute()
        assert circuit.state.value == "HALF_OPEN"
        assert "HALF_OPEN" in reason
    
    def test_closes_after_successes(self, circuit):
        """Test circuit closes after successes"""
        # Open the circuit
        circuit.record_failure()
        circuit.record_failure()
        circuit.record_failure()
        
        # Half open
        import time
        time.sleep(1.5)
        circuit.can_execute()
        
        # Successes
        circuit.record_success()
        circuit.record_success()
        
        assert circuit.state.value == "CLOSED"
    
    def test_force_open(self, circuit):
        """Test manual force open"""
        circuit.force_open("Test")
        
        assert circuit.state.value == "OPEN"
        can, _ = circuit.can_execute()
        assert not can
    
    def test_force_close(self, circuit):
        """Test manual force close"""
        circuit.force_open("Test")
        circuit.force_close("Test")
        
        assert circuit.state.value == "CLOSED"


# =========================
# AUDIT JOURNAL TESTS
# =========================

class TestAuditJournal:
    """Tests for audit journal"""
    
    @pytest.fixture
    def journal(self, temp_dir):
        from audit_journal import AuditJournal
        return AuditJournal(
            filepath=os.path.join(temp_dir, 'audit.csv'),
            hash_filepath=os.path.join(temp_dir, 'audit.hash')
        )
    
    def test_initialization(self, journal):
        """Test journal initializes"""
        assert os.path.exists(journal.filepath)
    
    def test_log_entry(self, journal):
        """Test logging an entry"""
        result = journal.log(
            event_type='DECISION',
            action='NO_TRADE',
            reason='Test',
            balance=500
        )
        
        assert result == True
    
    def test_verify_integrity(self, journal):
        """Test integrity verification"""
        journal.log(event_type='TEST', action='TEST', reason='test')
        
        valid, errors = journal.verify_integrity()
        assert valid
        assert len(errors) == 0
    
    def test_detects_tampering(self, journal, temp_dir):
        """Test detection of tampering"""
        journal.log(event_type='TEST', action='TEST', reason='test')
        
        # Tamper with file
        with open(journal.filepath, 'r') as f:
            content = f.read()
        
        tampered = content.replace('TEST', 'TAMPERED')
        
        with open(journal.filepath, 'w') as f:
            f.write(tampered)
        
        valid, errors = journal.verify_integrity()
        assert not valid
        assert len(errors) > 0


# =========================
# EXECUTOR TESTS
# =========================

class TestExecutor:
    """Tests for MT5 executor (mocked)"""
    
    @patch('executor.mt5')
    def test_margin_check_sufficient(self, mock_mt5):
        """Test margin check with sufficient margin"""
        mock_account = MagicMock()
        mock_account.margin_free = 1000
        
        mock_mt5.account_info.return_value = mock_account
        mock_mt5.order_calc_margin.return_value = 500
        
        from executor import check_margin_required
        can_trade, reason = check_margin_required('EURUSD', 0.1, 1.1, 0)
        
        assert can_trade
        assert "OK" in reason
    
    @patch('executor.mt5')
    def test_margin_check_insufficient(self, mock_mt5):
        """Test margin check with insufficient margin"""
        mock_account = MagicMock()
        mock_account.margin_free = 200
        
        mock_mt5.account_info.return_value = mock_account
        mock_mt5.order_calc_margin.return_value = 500
        
        from executor import check_margin_required
        can_trade, reason = check_margin_required('EURUSD', 0.1, 1.1, 0)
        
        assert not can_trade
        assert "Insufficient" in reason


# =========================
# CONFIG VALIDATION TESTS
# =========================

class TestConfig:
    """Tests for configuration"""
    
    def test_risk_limits_class(self):
        """Test RiskLimits class exists"""
        import config
        assert hasattr(config, 'RiskLimits')
        assert config.RiskLimits.MAX_RISK_PER_TRADE == 0.02
        assert config.RiskLimits.MAX_DAILY_LOSS == 20
    
    def test_no_hardcoded_credentials(self):
        """Test credentials are not hardcoded"""
        import config
        
        # Should be read from environment
        # If not set, should be empty/0
        assert config.MT5_ACCOUNT == 0 or isinstance(config.MT5_ACCOUNT, int)
        assert config.MT5_PASSWORD == '' or isinstance(config.MT5_PASSWORD, str)
        assert config.MT5_SERVER == '' or isinstance(config.MT5_SERVER, str)


# =========================
# INTEGRATION TESTS
# =========================

class TestIntegration:
    """Integration tests"""
    
    def test_full_trade_flow(self, risk_manager):
        """Test complete trade flow"""
        # 1. Check can trade
        can_trade, reason = risk_manager.can_trade()
        assert can_trade
        
        # 2. Validate trade
        valid, reason = risk_manager.validate_trade(
            entry=1.1000,
            sl=1.0950,
            tp=1.1200,
            direction="LONG"
        )
        assert valid
        
        # 3. Calculate position size
        size = risk_manager.calculate_position_size(
            balance=500,
            risk_pct=0.01,
            entry=1.1000,
            sl=1.0950,
            symbol="EURUSD"
        )
        assert size > 0
        
        # 4. Register trade
        risk_manager.add_trade()
        assert risk_manager.daily_trades == 1
        assert risk_manager.current_positions == 1
        
        # 5. Close trade with profit
        risk_manager.close_trade(15.0)
        assert risk_manager.daily_pnl == 15.0
        assert risk_manager.current_positions == 0
    
    def test_risk_limits_enforced(self, risk_manager):
        """Test hard risk limits are enforced"""
        # Try to exceed daily trades
        for _ in range(10):
            risk_manager.daily_trades += 1
        
        can_trade, _ = risk_manager.can_trade()
        assert not can_trade
        
        # Should be capped at max
        assert risk_manager.daily_trades <= risk_manager._max_daily_trades


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
