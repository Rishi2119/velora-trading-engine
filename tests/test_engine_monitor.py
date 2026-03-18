"""
Phase 13 test gate — Engine Monitoring & WebSocket feed
Run: python -m pytest tests/test_engine_monitor.py -v
"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.monitoring.engine_monitor import EngineMonitor, HealthStatus


@pytest.mark.asyncio
class TestEngineMonitor:
    
    async def test_health_snapshot_healthy(self):
        monitor = EngineMonitor()
        
        with patch('backend.app.monitoring.engine_monitor.mt5_conn') as mock_mt5, \
             patch.object(monitor, '_check_memory', return_value=120.5), \
             patch('backend.app.monitoring.engine_monitor.config') as mock_config:
             
             mock_config.engine_mode = "live"
             mock_mt5.is_connected.return_value = True
             
             snapshot = await monitor.get_health_snapshot()
             assert snapshot["status"] == HealthStatus.HEALTHY
             assert snapshot["engine_mode"] == "live"
             assert snapshot["mt5_connected"] is True
             assert snapshot["memory_usage_mb"] == 120.5
             assert len(snapshot["reasons"]) == 0

    async def test_health_snapshot_critical(self):
        monitor = EngineMonitor()
        
        with patch('backend.app.monitoring.engine_monitor.mt5_conn') as mock_mt5, \
             patch.object(monitor, '_check_memory', return_value=150.0), \
             patch('backend.app.monitoring.engine_monitor.config') as mock_config:
             
             mock_config.engine_mode = "live"
             mock_mt5.is_connected.return_value = False # Disconnected indicates critical!
             
             snapshot = await monitor.get_health_snapshot()
             assert snapshot["status"] == HealthStatus.CRITICAL
             assert snapshot["mt5_connected"] is False
             assert "MT5 Terminal Disconnected" in snapshot["reasons"]

    async def test_health_snapshot_degraded_memory(self):
        monitor = EngineMonitor()
        
        with patch('backend.app.monitoring.engine_monitor.mt5_conn') as mock_mt5, \
             patch.object(monitor, '_check_memory', return_value=650.5), \
             patch('backend.app.monitoring.engine_monitor.config') as mock_config:
             
             mock_config.engine_mode = "live"
             mock_mt5.is_connected.return_value = True
             
             snapshot = await monitor.get_health_snapshot()
             assert snapshot["status"] == HealthStatus.DEGRADED
             assert len(snapshot["reasons"]) == 1
             assert "High memory usage" in snapshot["reasons"][0]
