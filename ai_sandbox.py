"""
AI Sandbox - Sandboxed AI Execution Wrapper
Ensures AI can ONLY suggest trades, never execute directly
All AI suggestions must go through risk validation
"""

import time
import logging
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class AISandbox:
    """
    Sandboxed AI execution wrapper for safe AI trading.
    
    Key features:
    - AI can ONLY suggest trades, never execute directly
    - All suggestions go through risk validation
    - Human-in-the-loop required for execution
    - Rate limiting on AI calls
    - Deterministic fallback on AI failure
    """
    
    def __init__(self, risk_manager, config: Optional[Dict] = None):
        self.risk_manager = risk_manager
        self.config = config or {}
        
        # Security settings
        self.ai_enabled = self.config.get('ai_enabled', False)  # Default OFF
        self.ai_can_execute = False  # AI NEVER has direct execution
        self.min_confidence = self.config.get('min_confidence', 70)
        
        # Rate limiting
        self.max_calls = self.config.get('max_ai_calls_per_minute', 10)
        self.call_timestamps = []
        
        # Fallback
        self.fallback_action = "NO_TRADE"
        
        # Logging
        self.log_file = self.config.get('log_file', 'logs/ai_sandbox.log')
        self._ensure_log_dir()
        
        logger.info(f"AISandbox initialized: ai_enabled={self.ai_enabled}, "
                   f"ai_can_execute={self.ai_can_execute}, min_confidence={self.min_confidence}")
    
    def _ensure_log_dir(self):
        """Ensure log directory exists"""
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    def _log(self, level: str, message: str, data: Optional[Dict] = None):
        """Log AI decision"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "data": data or {}
        }
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write AI log: {e}")
        
        # Also log to main logger
        getattr(logger, level.lower())(message)
    
    # =========================
    # RATE LIMITING
    # =========================
    
    def _check_rate_limit(self) -> bool:
        """Check if AI call is within rate limit"""
        now = time.time()
        self.call_timestamps = [t for t in self.call_timestamps if now - t < 60]
        
        if len(self.call_timestamps) >= self.max_calls:
            self._log("warning", "AI rate limit exceeded", {"calls": len(self.call_timestamps)})
            return False
        
        self.call_timestamps.append(now)
        return True
    
    # =========================
    # VALIDATION
    # =========================
    
    def _validate_signal_structure(self, signal: Dict) -> Tuple[bool, str]:
        """Validate AI signal has required fields"""
        required = ['direction', 'entry', 'sl', 'tp', 'symbol', 'confidence']
        
        for field in required:
            if field not in signal:
                return False, f"Missing required field: {field}"
        
        # Validate direction
        if signal['direction'].upper() not in ['LONG', 'SHORT']:
            return False, f"Invalid direction: {signal['direction']}"
        
        # Validate numeric fields
        for field in ['entry', 'sl', 'tp', 'confidence']:
            try:
                float(signal[field])
            except (ValueError, TypeError):
                return False, f"Invalid {field}: {signal[field]}"
        
        return True, "OK"
    
    def _validate_confidence(self, confidence: float) -> Tuple[bool, str]:
        """Validate AI confidence meets threshold"""
        if confidence < self.min_confidence:
            return False, f"Confidence {confidence}% below threshold {self.min_confidence}%"
        
        if confidence > 100:
            return False, f"Invalid confidence: {confidence}%"
        
        return True, "OK"
    
    # =========================
    # MAIN INTERFACE
    # =========================
    
    def request_trade(self, ai_signal: Dict, balance: float) -> Dict:
        """
        Process AI signal through sandbox.
        
        This is the MAIN entry point for AI trade requests.
        
        Args:
            ai_signal: Dict with keys: direction, entry, sl, tp, symbol, confidence
            balance: Current account balance for risk calculation
            
        Returns:
            Dict with keys: approved (bool), reason (str), validated_params (dict or None)
        """
        self._log("info", "AI trade request received", {"signal": ai_signal})
        
        # Check rate limiting
        if not self._check_rate_limit():
            return {
                "approved": False,
                "reason": "Rate limit exceeded",
                "validated_params": None,
                "action": self.fallback_action
            }
        
        # Check if AI is enabled
        if not self.ai_enabled:
            self._log("warning", "AI disabled - rejecting request")
            return {
                "approved": False,
                "reason": "AI trading is disabled",
                "validated_params": None,
                "action": self.fallback_action
            }
        
        # AI can NEVER execute directly - this is a hard security rule
        if self.ai_can_execute:
            self._log("error", "SECURITY: ai_can_execute should NEVER be True!")
            return {
                "approved": False,
                "reason": "Security error: AI execution flag is True (should never happen)",
                "validated_params": None,
                "action": self.fallback_action
            }
        
        # Validate signal structure
        valid, reason = self._validate_signal_structure(ai_signal)
        if not valid:
            self._log("warning", f"Invalid signal structure: {reason}")
            return {
                "approved": False,
                "reason": f"Invalid signal: {reason}",
                "validated_params": None,
                "action": self.fallback_action
            }
        
        # Validate confidence
        valid, reason = self._validate_confidence(ai_signal['confidence'])
        if not valid:
            self._log("warning", f"Low confidence rejected: {reason}")
            return {
                "approved": False,
                "reason": reason,
                "validated_params": None,
                "action": self.fallback_action
            }
        
        # Validate with risk manager
        valid, reason = self.risk_manager.validate_trade(
            entry=ai_signal['entry'],
            sl=ai_signal['sl'],
            tp=ai_signal['tp'],
            direction=ai_signal['direction'],
            min_rr=3.0  # Enforce minimum 3:1 RR
        )
        
        if not valid:
            self._log("warning", f"Risk validation failed: {reason}")
            return {
                "approved": False,
                "reason": f"Risk validation failed: {reason}",
                "validated_params": None,
                "action": self.fallback_action
            }
        
        # Check if can trade (daily limits, etc)
        can_trade, reason = self.risk_manager.can_trade()
        if not can_trade:
            self._log("warning", f"Cannot trade: {reason}")
            return {
                "approved": False,
                "reason": f"Cannot trade: {reason}",
                "validated_params": None,
                "action": self.fallback_action
            }
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            balance=balance,
            risk_pct=self.config.get('risk_per_trade', 0.01),
            entry=ai_signal['entry'],
            sl=ai_signal['sl'],
            symbol=ai_signal['symbol']
        )
        
        if position_size <= 0:
            self._log("warning", "Position size calculation returned 0")
            return {
                "approved": False,
                "reason": "Invalid position size",
                "validated_params": None,
                "action": self.fallback_action
            }
        
        # All validations passed
        # NOTE: We return validated_params but DON'T auto-execute
        # Human must approve execution
        validated = {
            "symbol": ai_signal['symbol'],
            "direction": ai_signal['direction'].upper(),
            "entry": float(ai_signal['entry']),
            "sl": float(ai_signal['sl']),
            "tp": float(ai_signal['tp']),
            "volume": position_size,
            "confidence": ai_signal['confidence'],
            "rr": self.risk_manager.calculate_rr(ai_signal['entry'], ai_signal['sl'], ai_signal['tp'])
        }
        
        self._log("info", "AI signal approved (awaiting human confirmation)", validated)
        
        return {
            "approved": True,
            "reason": "Signal validated and approved for execution",
            "validated_params": validated,
            "action": "WAIT_FOR_CONFIRMATION"
        }
    
    # =========================
    # CONFIGURATION
    # =========================
    
    def enable_ai(self):
        """Enable AI analysis (but NOT direct execution)"""
        self.ai_enabled = True
        self._log("info", "AI enabled (analysis only)")
    
    def disable_ai(self):
        """Disable AI completely"""
        self.ai_enabled = False
        self._log("info", "AI disabled")
    
    def set_min_confidence(self, confidence: int):
        """Set minimum confidence threshold"""
        self.min_confidence = max(50, min(95, confidence))
        self._log("info", f"Minimum confidence set to {self.min_confidence}%")
    
    def get_status(self) -> Dict:
        """Get sandbox status"""
        return {
            "ai_enabled": self.ai_enabled,
            "ai_can_execute": self.ai_can_execute,
            "min_confidence": self.min_confidence,
            "rate_limit_remaining": self.max_calls - len([t for t in self.call_timestamps if time.time() - t < 60]),
            "max_calls_per_minute": self.max_calls
        }
    
    # =========================
    # FALLBACK HANDLER
    # =========================
    
    def handle_ai_failure(self, error: Exception) -> Dict:
        """Handle AI failure - always return safe fallback"""
        self._log("error", f"AI failure: {str(error)}", {"error_type": type(error).__name__})
        
        return {
            "approved": False,
            "reason": f"AI error: {str(error)}",
            "validated_params": None,
            "action": self.fallback_action,
            "is_fallback": True
        }
