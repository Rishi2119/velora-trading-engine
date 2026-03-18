"""
Phase 12: Copy Trading Module.
Provides publisher/subscriber classes for internal signal mirroring across accounts or engines.
"""
import time
import logging
import threading
from collections import deque
from typing import Optional, List, Tuple

from backend.app.strategies.strategy_manager import BaseStrategy, SignalResult
from backend.app.engine.feature_engine import FeatureSet
from backend.app.strategies.regime_detector import RegimeResult

logger = logging.getLogger(__name__)


class CopyBroadcaster:
    """Publishes execution signals to an internal memory queue for followers."""
    
    def __init__(self, maxsize=100):
        self._lock = threading.RLock()
        self._queue: deque = deque(maxlen=maxsize)
        
    def broadcast(self, signal: SignalResult) -> None:
        """Add a signal to the broadcast queue with a timestamp."""
        with self._lock:
            self._queue.append((time.time(), signal))
            logger.info(f"Broadcasted Copy Signal: {signal.direction} {signal.symbol}")
            
    def get_recent_signals(self, symbol: str, max_age_seconds: float = 30.0) -> List[SignalResult]:
        """Fetch unexpired signals for a specific symbol."""
        valid_signals = []
        now = time.time()
        
        with self._lock:
            # We copy the queue to avoid mid-iteration mutations, since deque is thread-safe
            # for append/pop but not iteration. Lock protects it.
            for ts, sig in list(self._queue):
                if sig.symbol == symbol and (now - ts) <= max_age_seconds:
                    valid_signals.append(sig)
                    
        return valid_signals

# Singleton Broadcaster for cross-thread emission
copy_broadcaster = CopyBroadcaster()


class CopyFollower(BaseStrategy):
    """
    Subscribes to CopyBroadcaster. 
    Returns the copied signal if it's within the stale timeout window.
    Acts exactly like a normal AI/Trend strategy to the StrategyManager.
    """
    
    def __init__(self, stale_timeout_seconds: float = 30.0):
        self._name = "Copy_Follower"
        self.stale_timeout = stale_timeout_seconds
        
    @property
    def name(self) -> str:
        return self._name
        
    def evaluate(self, features: FeatureSet, regime: RegimeResult) -> Optional[SignalResult]:
        """Check for active broadcasts. Return the freshest valid one."""
        recent = copy_broadcaster.get_recent_signals(features.symbol, max_age_seconds=self.stale_timeout)
        
        if not recent:
            return None
            
        # We take the most recently broadcasted signal (last in list)
        best_signal = recent[-1]
        
        logger.info(f"CopyFollower picked up signal: {best_signal.direction} {best_signal.symbol}")
        
        # We wrap it in a new SignalResult so the engine sees "Copy_Follower" as the originator,
        # but preserving the entry, sl, tp, and injecting max confidence since it's a mirror trade.
        return SignalResult(
            strategy_name=self.name,
            symbol=features.symbol,
            direction=best_signal.direction,
            confidence=100.0, # Complete override confidence
            entry=best_signal.entry,
            sl=best_signal.sl,
            tp=best_signal.tp,
            reason=f"Copied from {best_signal.strategy_name}"
        )
