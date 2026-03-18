"""
Phase 12 test gate — Copy Trading tests.
Run: python -m pytest tests/test_copy_trading.py -v
"""
import sys
import os
import time
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.strategies.copy_trading import CopyBroadcaster, CopyFollower
from backend.app.strategies.strategy_manager import SignalResult
from backend.app.engine.feature_engine import FeatureSet
from backend.app.strategies.regime_detector import RegimeResult


class TestCopyTrading:
    
    def test_broadcast_and_receive(self):
        broadcaster = CopyBroadcaster()
        follower = CopyFollower(stale_timeout_seconds=30.0)
        
        # Patch the singleton in the module so follower uses our local broadcaster
        with patch('backend.app.strategies.copy_trading.copy_broadcaster', broadcaster):
            
            sig = SignalResult("TestStrat", "EURUSD", "BUY", 95.0, 1.10, 1.09, 1.12, "Test")
            broadcaster.broadcast(sig)
            
            # Create dummy features/regime
            mock_features = MagicMock(spec=FeatureSet)
            mock_features.symbol = "EURUSD"
            mock_regime = MagicMock(spec=RegimeResult)
            
            result = follower.evaluate(mock_features, mock_regime)
            
            assert result is not None
            assert result.strategy_name == "Copy_Follower"
            assert result.direction == "BUY"
            assert result.confidence == 100.0
            assert "Copied from TestStrat" in result.reason
            
    def test_stale_signal_timeout(self):
        broadcaster = CopyBroadcaster()
        follower = CopyFollower(stale_timeout_seconds=0.1) # 100ms timeout
        
        with patch('backend.app.strategies.copy_trading.copy_broadcaster', broadcaster):
            
            sig = SignalResult("TestStrat", "GBPUSD", "SELL", 90.0, 1.30, 1.31, 1.28, "Test")
            broadcaster.broadcast(sig)
            
            time.sleep(0.2) # Wait for signal to expire
            
            mock_features = MagicMock(spec=FeatureSet)
            mock_features.symbol = "GBPUSD"
            mock_regime = MagicMock(spec=RegimeResult)
            
            result = follower.evaluate(mock_features, mock_regime)
            
            # Should be strictly None since the signal expired
            assert result is None
