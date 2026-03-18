"""
Phase 13: System Monitoring Daemon.
Periodically assesses the health of the execution engine, database, and subsystems.
Broadcasts state changes to the frontend via WebSocket.
"""
import asyncio
import logging
import psutil
from typing import Dict, Any
from datetime import datetime, UTC

from backend.app.execution.mt5_connection import mt5_conn
from backend.app.core.config import config
from backend.ws.feed import manager as ws_manager

logger = logging.getLogger(__name__)


class HealthStatus:
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


class EngineMonitor:
    """Monitors system components and broadcasts telemetrics."""
    
    def __init__(self, check_interval_sec: int = 5):
        self.check_interval_sec = check_interval_sec
        self._is_running = False
        self._last_status = HealthStatus.HEALTHY
        
    def _check_memory(self) -> float:
        """Return process memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
        
    async def get_health_snapshot(self) -> Dict[str, Any]:
        """Aggregate health status of all components."""
        
        # 1. Component checks
        mt5_ok = mt5_conn.is_connected() if config.engine_mode == "live" else True
        memory_mb = self._check_memory()
        
        # Determine global state
        status = HealthStatus.HEALTHY
        reasons = []
        
        if config.engine_mode == "live" and not mt5_ok:
            status = HealthStatus.CRITICAL
            reasons.append("MT5 Terminal Disconnected")
            
        if memory_mb > 500: # 500MB is unusually high for our pure python backend
            if status != HealthStatus.CRITICAL:
                status = HealthStatus.DEGRADED
            reasons.append(f"High memory usage: {memory_mb:.1f}MB")
            
        return {
            "status": status,
            "engine_mode": config.engine_mode,
            "mt5_connected": mt5_ok,
            "memory_usage_mb": round(memory_mb, 1),
            "reasons": reasons,
            "timestamp": datetime.now(UTC).isoformat()
        }

    async def _monitor_loop(self):
        logger.info("Engine Monitor background loop started.")
        while self._is_running:
            try:
                snapshot = await self.get_health_snapshot()
                
                # We always broadcast the current heartbeats
                await ws_manager.broadcast("health_heartbeat", snapshot)
                
                # Check state transition for alerts
                current_status = snapshot["status"]
                if current_status != self._last_status:
                    logger.warning(f"System health changed: {self._last_status} -> {current_status}")
                    await ws_manager.broadcast("health_alert", {
                        "previous": self._last_status,
                        "current": current_status,
                        "reasons": snapshot["reasons"]
                    }, severity="warning" if current_status == HealthStatus.DEGRADED else "critical")
                    self._last_status = current_status
                    
            except Exception as e:
                logger.error(f"Engine Monitor loop error: {e}")
                
            await asyncio.sleep(self.check_interval_sec)
            
    def start(self):
        """Start the background monitor task."""
        if self._is_running:
            return
            
        self._is_running = True
        logger.info("Initializing EngineMonitor...")
        asyncio.create_task(self._monitor_loop())
        
    def stop(self):
        """Stop the background monitor task."""
        self._is_running = False
        logger.info("EngineMonitor stopped.")

# Singleton
engine_monitor = EngineMonitor()
