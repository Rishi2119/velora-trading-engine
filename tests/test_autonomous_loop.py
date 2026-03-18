"""
Phase 7 test gate — Autonomous Engine smoke test.
Run: python -m pytest tests/test_autonomous_loop.py -v
"""
import sys
import os
import time
import pytest
import logging
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.engine.autonomous_loop import AutonomousEngine
from backend.app.core.config import config


class TestAutonomousEngine:
    
    @patch('backend.app.engine.autonomous_loop.mt5_conn')
    def test_paper_mode_smoke_test(self, mock_mt5_conn, caplog):
        """
        Verify the engine can start, run in the background for a few seconds,
        and shutdown cleanly without crashing the main thread.
        """
        caplog.set_level(logging.INFO)
        
        # Force Paper mode
        original_mode = config.engine_mode
        config.engine_mode = "paper"
        
        # Don't actually fetch MT5 data
        mock_mt5_conn.get_rates.return_value = None
        
        engine = AutonomousEngine()
        
        try:
            # 1. Start
            success = engine.start()
            assert success is True
            assert engine.is_running is True
            
            # 2. Let it heartbeat for 2 seconds
            time.sleep(2.0)
            
            # 3. Stop
            engine.stop()
            
            # 4. Verify clean shutdown
            assert engine.is_running is False
            
            # Check logs for expected startup/shutdown sequences
            log_messages = [record.message for record in caplog.records]
            assert any("Starting Autonomous Engine" in msg for msg in log_messages)
            assert any("Autonomous Engine started successfully" in msg for msg in log_messages)
            assert any("Stopping Autonomous Engine" in msg for msg in log_messages)
            assert any("Autonomous Engine stopped gracefully" in msg for msg in log_messages)
            
        finally:
            engine.stop()
            config.engine_mode = original_mode
            
    def test_live_mode_requires_mt5(self, caplog):
        """Verify the engine refuses to start in LIVE mode if MT5 is unavailable/disconnected."""
        with patch('backend.app.engine.autonomous_loop.mt5_conn') as mock_mt5_conn:
            original_mode = config.engine_mode
            config.engine_mode = "live"
            
            # Simulate MT5 not connecting
            mock_mt5_conn.is_connected = False
            mock_mt5_conn.connect.return_value = False
            
            engine = AutonomousEngine()
            
            try:
                success = engine.start()
                assert success is False
                assert engine.is_running is False
            finally:
                engine.stop()
                config.engine_mode = original_mode
