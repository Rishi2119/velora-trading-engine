"""
Circuit Breaker - Production Circuit Breaker Pattern
Protects against cascading failures in trading system
"""

import time
import threading
import logging
from enum import Enum
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for trading system protection.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject all requests
    - HALF_OPEN: Testing if service recovered
    
    Configuration:
    - failure_threshold: Number of failures before opening
    - success_threshold: Number of successes to close from half-open
    - timeout: Seconds to wait before attempting recovery
    """
    
    def __init__(self, name: str, failure_threshold: int = 5, 
                 success_threshold: int = 2, timeout: int = 60,
                 log_file: str = "logs/circuit_breaker.log"):
        
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        
        self._lock = threading.RLock()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._opened_at = None
        
        self.log_file = log_file
        self._ensure_log_dir()
        
        logger.info(f"CircuitBreaker '{name}' initialized: "
                   f"failure_threshold={failure_threshold}, timeout={timeout}s")
    
    def _ensure_log_dir(self):
        """Ensure log directory exists"""
        log_dir = self.log_file.split('/')
        if len(log_dir) > 1:
            import os
            dir_path = '/'.join(log_dir[:-1])
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
    
    def _log(self, level: str, message: str):
        """Log circuit breaker event"""
        timestamp = datetime.now().isoformat()
        log_entry = f'{{"timestamp": "{timestamp}", "circuit": "{self.name}", "state": "{self._state.value}", "level": "{level}", "message": "{message}"}}\n'
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry)
        except Exception:
            pass
        
        getattr(logger, level.lower())(f"[{self.name}] {message}")
    
    # =========================
    # STATE MANAGEMENT
    # =========================
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        with self._lock:
            self._check_timeout()
            return self._state
    
    def _check_timeout(self):
        """Check if timeout has passed to transition from OPEN to HALF_OPEN"""
        if self._state == CircuitState.OPEN and self._opened_at:
            elapsed = time.time() - self._opened_at
            if elapsed >= self.timeout:
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                self._log("info", f"Timeout elapsed, transitioning to HALF_OPEN (elapsed: {elapsed:.1f}s)")
    
    # =========================
    # MAIN INTERFACE
    # =========================
    
    def can_execute(self) -> tuple[bool, str]:
        """
        Check if execution is allowed.
        
        Returns:
            (can_execute, reason)
        """
        with self._lock:
            self._check_timeout()
            
            if self._state == CircuitState.CLOSED:
                return True, "OK"
            
            elif self._state == CircuitState.OPEN:
                elapsed = time.time() - self._opened_at if self._opened_at else 0
                return False, f"Circuit OPEN (opened {elapsed:.0f}s ago, timeout: {self.timeout}s)"
            
            elif self._state == CircuitState.HALF_OPEN:
                return True, "Circuit HALF_OPEN - testing recovery"
            
            return False, "Unknown circuit state"
    
    def record_success(self):
        """Record a successful operation"""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                self._log("info", f"Success recorded ({self._success_count}/{self.success_threshold})")
                
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._log("info", "Circuit CLOSED - recovery successful")
            
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                if self._failure_count > 0:
                    self._failure_count = 0
    
    def record_failure(self, error: Optional[str] = None):
        """Record a failed operation"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            error_msg = f" - {error}" if error else ""
            self._log("warning", f"Failure recorded ({self._failure_count}/{self.failure_threshold}){error_msg}")
            
            if self._state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN goes back to OPEN
                self._state = CircuitState.OPEN
                self._opened_at = time.time()
                self._log("error", "Circuit re-OPENED due to failure during HALF_OPEN")
            
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    self._opened_at = time.time()
                    self._log("error", f"Circuit OPENED after {self._failure_count} failures")
    
    def force_open(self, reason: str = "Manual"):
        """Manually open the circuit"""
        with self._lock:
            self._state = CircuitState.OPEN
            self._opened_at = time.time()
            self._log("warning", f"Circuit manually OPENED: {reason}")
    
    def force_close(self, reason: str = "Manual"):
        """Manually close the circuit"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._log("info", f"Circuit manually CLOSED: {reason}")
    
    def reset(self):
        """Reset the circuit to initial state"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._opened_at = None
            self._log("info", "Circuit reset to initial state")
    
    # =========================
    # STATUS
    # =========================
    
    def get_status(self) -> Dict:
        """Get circuit breaker status"""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "failure_threshold": self.failure_threshold,
                "success_threshold": self.success_threshold,
                "timeout": self.timeout,
                "last_failure": datetime.fromtimestamp(self._last_failure_time).isoformat() if self._last_failure_time else None,
                "opened_at": datetime.fromtimestamp(self._opened_at).isoformat() if self._opened_at else None
            }
    
    def __repr__(self):
        return f"CircuitBreaker(name='{self.name}', state={self._state.value}, failures={self._failure_count})"


class CircuitBreakerManager:
    """Manages multiple circuit breakers for different services"""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
    
    def get_or_create(self, name: str, **kwargs) -> CircuitBreaker:
        """Get existing or create new circuit breaker"""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, **kwargs)
            return self._breakers[name]
    
    def get_all_status(self) -> Dict:
        """Get status of all circuit breakers"""
        return {name: breaker.get_status() for name, breaker in self._breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self._breakers.values():
            breaker.reset()
