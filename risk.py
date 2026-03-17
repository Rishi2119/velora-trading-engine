"""
Production Risk Manager - FIXED VERSION
Thread-safe risk management with proper pip calculation and daily reset
"""

import threading
import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import Tuple, Dict, Any, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskManager:
    """
    Thread-safe production risk manager with:
    - Proper pip calculation for all pairs (JPY/non-JPY)
    - Automatic daily reset at midnight
    - State persistence to disk
    - Hard risk limits
    """
    
    def __init__(self, max_daily_loss: float, max_daily_trades: int, 
                 max_concurrent: int, risk_per_trade: float = 0.01,
                 min_rr: float = 3.0, state_file: str = "logs/risk_state.json"):
        
        self._lock = threading.RLock()
        
        # Hard limits (cannot be exceeded)
        self._max_risk_per_trade = 0.02  # 2% absolute max
        self._max_daily_loss = max(max_daily_loss, 20)  # Min $20
        self._max_daily_trades = min(max_daily_trades, 10)  # Max 10
        self._max_concurrent = min(max_concurrent, 3)  # Max 3
        
        # Configured values (capped at hard limits)
        self.risk_per_trade = min(risk_per_trade, self._max_risk_per_trade)
        self.min_rr = min_rr
        
        # State
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.current_positions = 0
        self.last_reset_date = date.today()
        self._morning_reset_done = False
        
        # Persistence
        self.state_file = state_file
        self._ensure_state_dir()
        self._load_state()
        
        logger.info(f"RiskManager initialized: max_daily_loss=${self._max_daily_loss}, "
                   f"max_trades={self._max_daily_trades}, max_concurrent={self._max_concurrent}")
    
    def _ensure_state_dir(self):
        """Ensure state directory exists"""
        state_dir = os.path.dirname(self.state_file)
        if state_dir and not os.path.exists(state_dir):
            os.makedirs(state_dir, exist_ok=True)
    
    # =========================
    # STATE PERSISTENCE
    # =========================
    
    def _load_state(self):
        """Load persisted state from disk"""
        if not os.path.exists(self.state_file):
            return
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                self.daily_pnl = state.get('daily_pnl', 0.0)
                self.daily_trades = state.get('daily_trades', 0)
                self.last_reset_date = date.fromisoformat(
                    state.get('last_reset_date', str(date.today()))
                )
                logger.info(f"Loaded state: date={self.last_reset_date}, pnl={self.daily_pnl}")
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
    
    def _save_state(self):
        """Persist state to disk"""
        try:
            state = {
                'daily_pnl': self.daily_pnl,
                'daily_trades': self.daily_trades,
                'last_reset_date': str(self.last_reset_date)
            }
            tmp_file = self.state_file + '.tmp'
            with open(tmp_file, 'w') as f:
                json.dump(state, f)
            os.replace(tmp_file, self.state_file)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    # =========================
    # DAILY RESET
    # =========================
    
    def _check_daily_reset(self):
        """Check and perform daily reset if needed"""
        today = date.today()
        
        # Reset if new day
        if today > self.last_reset_date:
            logger.info(f"Daily reset: {self.last_reset_date} -> {today}")
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.last_reset_date = today
            self._save_state()
        
        # Also check for midnight crossing (for long-running processes)
        current_time = datetime.now()
        if current_time.hour < 6 and hasattr(self, '_morning_reset_done'):
            if not self._morning_reset_done:
                self.daily_pnl = 0.0
                self.daily_trades = 0
                self._morning_reset_done = True
                self._save_state()
        elif current_time.hour >= 6:
            self._morning_reset_done = False
    
    # =========================
    # PERMISSION CHECK
    # =========================
    
    def can_trade(self) -> Tuple[bool, str]:
        """Check if trading is permitted"""
        with self._lock:
            self._check_daily_reset()
            
            if self.daily_pnl <= -self._max_daily_loss:
                return False, f"MAX DAILY LOSS REACHED: ${self.daily_pnl:.2f} / ${self._max_daily_loss}"
            
            if self.daily_trades >= self._max_daily_trades:
                return False, f"MAX DAILY TRADES: {self.daily_trades} / {self._max_daily_trades}"
            
            if self.current_positions >= self._max_concurrent:
                return False, f"MAX CONCURRENT POSITIONS: {self.current_positions} / {self._max_concurrent}"
            
            return True, "OK"
    
    # =========================
    # TRADE REGISTRATION
    # =========================
    
    def add_trade(self, pnl: float = 0):
        """Register a new trade"""
        with self._lock:
            self.daily_trades += 1
            self.current_positions += 1
            self.daily_pnl += pnl
            self._save_state()
            logger.info(f"Trade opened: daily_trades={self.daily_trades}, "
                       f"positions={self.current_positions}, pnl=${self.daily_pnl:.2f}")
    
    def close_trade(self, pnl: float):
        """Register trade closure"""
        with self._lock:
            self.daily_pnl += pnl
            self.current_positions = max(0, self.current_positions - 1)
            self._save_state()
            logger.info(f"Trade closed: pnl=${pnl:.2f}, total_pnl=${self.daily_pnl:.2f}, "
                       f"positions={self.current_positions}")
    
    # =========================
    # DAILY RESET (manual)
    # =========================
    
    def reset_daily(self):
        """Manually reset daily counters"""
        with self._lock:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.last_reset_date = date.today()
            self._save_state()
            logger.info("Daily counters manually reset")
    
    # =========================
    # VALIDATE RR
    # =========================
    
    def validate_trade(self, entry: float, sl: float, tp: float, 
                       direction: str, min_rr: Union[float, None] = None) -> Tuple[bool, str]:
        """Validate trade parameters including RR"""
        if min_rr is None:
            min_rr = self.min_rr
        
        # Validate direction
        direction = direction.upper()
        if direction not in ['LONG', 'SHORT']:
            return False, f"Invalid direction: {direction}"
        
        # Validate stops
        if direction == "LONG":
            if sl >= entry:
                return False, "SL must be below entry for LONG"
            if tp <= entry:
                return False, "TP must be above entry for LONG"
            risk = entry - sl
            reward = tp - entry
        else:  # SHORT
            if sl <= entry:
                return False, "SL must be above entry for SHORT"
            if tp >= entry:
                return False, "TP must be below entry for SHORT"
            risk = sl - entry
            reward = entry - tp
        
        if risk <= 0:
            return False, "Invalid stop loss (zero or negative risk)"
        
        # Calculate RR
        rr = reward / risk
        
        if rr < min_rr:
            return False, f"RR {rr:.2f} below minimum {min_rr}:1"
        
        return True, f"Valid (RR={rr:.2f})"
    
    # =========================
    # POSITION SIZE (FOREX)
    # =========================
    
    def calculate_position_size(self, balance: float, risk_pct: float, 
                                entry: float, sl: float, symbol: str) -> float:
        """
        Calculate position size with PROPER pip calculation
        Handles JPY pairs (100x) and non-JPY pairs (10000x)
        """
        with self._lock:
            # Cap risk at hard limit
            risk_pct = min(risk_pct, self._max_risk_per_trade)
            
            risk_amount = balance * risk_pct
            stop_distance = abs(entry - sl)
            
            if stop_distance <= 0:
                logger.warning(f"Invalid stop distance for {symbol}: {stop_distance}")
                return 0.0
            
            # Determine pip multiplier based on symbol
            symbol_upper = symbol.upper()
            if 'JPY' in symbol_upper:
                pip_multiplier = 100
            else:
                pip_multiplier = 10000
            
            stop_pips = stop_distance * pip_multiplier
            
            if stop_pips == 0:
                logger.warning(f"Zero pips for {symbol} (distance: {stop_distance})")
                return 0.0
            
            # Standard lot = 100,000 units = $10/pip for non-JPY, $1000/pip for JPY
            if 'JPY' in symbol_upper:
                lot_size = risk_amount / (stop_pips * 100)  # $100 per pip per lot for JPY
            else:
                lot_size = risk_amount / (stop_pips * 10)   # $10 per pip per lot
            
            # Round to 2 decimal places and cap
            lot_size = round(max(0.01, lot_size), 2)
            
            # Get max position size from config
            max_lot = 0.5  # Default max
            if hasattr(self, '_max_position_size'):
                max_lot = self._max_position_size
            
            lot_size = min(lot_size, max_lot)
            
            logger.info(f"Position size for {symbol}: {lot_size} lots "
                       f"(risk=${risk_amount:.2f}, stop={stop_pips:.1f} pips)")
            
            return lot_size
    
    def set_max_position_size(self, max_size: float):
        """Set maximum position size"""
        with self._lock:
            self._max_position_size = float(min(max_size, 1.0))  # Cap at 1 lot
            logger.info(f"Max position size set to {self._max_position_size}")
    
    # =========================
    # RR CALC
    # =========================
    
    def calculate_rr(self, entry: float, sl: float, tp: float) -> float:
        """Calculate risk:reward ratio"""
        risk = abs(entry - sl)
        if risk <= 0:
            return 0.0
        return round(abs(tp - entry) / risk, 2)
    
    # =========================
    # STATS
    # =========================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current risk statistics"""
        with self._lock:
            return {
                "daily_pnl": round(self.daily_pnl, 2),
                "daily_trades": self.daily_trades,
                "open_positions": self.current_positions,
                "max_daily_loss": self._max_daily_loss,
                "max_daily_trades": self._max_daily_trades,
                "max_concurrent": self._max_concurrent,
                "risk_per_trade": self.risk_per_trade,
                "min_rr": self.min_rr,
                "last_reset": str(self.last_reset_date)
            }
    
    def get_remaining(self) -> Dict[str, Any]:
        """Get remaining allowances"""
        with self._lock:
            return {
                "daily_loss_remaining": round(self._max_daily_loss + self.daily_pnl, 2),
                "trades_remaining": self._max_daily_trades - self.daily_trades,
                "positions_remaining": self._max_concurrent - self.current_positions
            }
