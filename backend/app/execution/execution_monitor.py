"""
Execution Monitor for tracking trade telemetry.
Monitors slippage, latency, and rejection rates, raising alerts if thresholds are breached.
"""
import logging
import threading
from typing import Dict, Any, List
from collections import deque
from datetime import datetime
import asyncio

from backend.app.core.config import config

# Optional real-time alert stub
def _send_telegram_alert(msg: str):
    logger.critical(f"TELEGRAM ALERT: {msg}")

logger = logging.getLogger(__name__)


class ExecutionMonitor:
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Keep last 50 executions in memory for rolling stats
        self.recent_trades: deque = deque(maxlen=50)
        self.rejection_count: int = 0
        self.last_rejection_reset: datetime = datetime.now()
        
    def log_execution(self, expected_price: float, exec_result: Dict[str, Any], latency_ms: float) -> None:
        """Record a completed or rejected trade execution attempt."""
        with self._lock:
            status = exec_result.get("status")
            
            if status == "REJECTED" or status == "ERROR":
                self._handle_rejection(exec_result.get("reason", "Unknown reason"))
                return
                
            if status == "FILLED":
                fill_price = exec_result.get("fill_price", expected_price)
                direction = exec_result.get("direction")
                symbol = exec_result.get("symbol")
                
                # Calculate Slippage (Points)
                # Assuming standard 0.00001 point size for forex if not provided
                slippage = 0.0
                if direction == "BUY":
                    slippage = fill_price - expected_price
                elif direction == "SELL":
                    slippage = expected_price - fill_price
                    
                trade_data = {
                    "timestamp": datetime.now(),
                    "symbol": symbol,
                    "direction": direction,
                    "expected_price": expected_price,
                    "fill_price": fill_price,
                    "slippage": slippage,
                    "latency_ms": latency_ms
                }
                
                self.recent_trades.append(trade_data)
                self._check_slippage_alert(trade_data)
                self._check_latency_alert(trade_data)
                
    def _handle_rejection(self, reason: str) -> None:
        """Track rejections and alert if too many happen within a time window."""
        now = datetime.now()
        
        # Reset counter every hour
        if (now - self.last_rejection_reset).total_seconds() > 3600:
            self.rejection_count = 0
            self.last_rejection_reset = now
            
        self.rejection_count += 1
        
        if self.rejection_count >= 3:
            msg = f"High Rejection Rate detected: 3+ rejections in the last hour. Latest reason: {reason}"
            logger.warning(msg)
            _send_telegram_alert(msg)
            
    def _check_slippage_alert(self, trade: Dict[str, Any]) -> None:
        """Alert if slippage exceeds anomalous threshold."""
        # Config max slippage is in Pips (1 pip = 10 points), 0.0001
        slippage_value = trade["slippage"]
        symbol = trade["symbol"]
        
        # Simple basic threshold: 5 pips (0.0005)
        # In a real app, this should use symbol point sizes dynamically,
        # but for safety monitor we assume EURUSD standard 5 pips = 0.0005
        if abs(slippage_value) > 0.0005: 
            msg = f"Heavy Slippage detected on {symbol}: {slippage_value:.5f}"
            logger.warning(msg)
            _send_telegram_alert(msg)

    def _check_latency_alert(self, trade: Dict[str, Any]) -> None:
        """Alert if broker execution latency is spiking."""
        # Alert if latency > 2000ms (2s)
        if trade["latency_ms"] > 2000.0:
            msg = f"High Execution Latency on {trade['symbol']}: {trade['latency_ms']:.1f}ms"
            logger.warning(msg)
            _send_telegram_alert(msg)
            
    def get_execution_stats(self) -> Dict[str, Any]:
        with self._lock:
            stats = {
                "trades_tracked": len(self.recent_trades),
                "rejections_this_hour": self.rejection_count,
                "avg_latency_ms": 0.0,
                "avg_slippage": 0.0
            }
            
            if self.recent_trades:
                stats["avg_latency_ms"] = round(sum(t["latency_ms"] for t in self.recent_trades) / len(self.recent_trades), 2)
                stats["avg_slippage"] = round(sum(t["slippage"] for t in self.recent_trades) / len(self.recent_trades), 6)
                
            return stats

# Singleton
execution_monitor = ExecutionMonitor()
