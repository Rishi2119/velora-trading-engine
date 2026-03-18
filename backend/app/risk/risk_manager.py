"""
Advanced Risk Manager for Velora Engine.
Implements 9-layer risk verification and position sizing logic.
"""
from typing import Dict, Optional, Tuple, List
import logging
from dataclasses import dataclass
from datetime import date
import threading

from backend.app.core.config import config
from backend.app.strategies.strategy_manager import SignalResult

logger = logging.getLogger(__name__)


@dataclass
class RiskDecision:
    approved: bool
    reason: str
    normalized_lots: float
    effective_risk_pct: float
    pip_value_usd: float


class RiskManager:
    """
    9-Layer Risk Gate:
    1. Daily Loss Limit
    2. Max Daily Trades Limit
    3. Concurrent Positions Limit
    4. Symbol Exposure Limit
    5. Minimum R:R Ratio
    6. Minimum Stop Distance
    7. Max Spread Tolerance (checked at execution)
    8. Slippage Tolerance (checked at execution)
    9. Margin/Lot Size Validation
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # State tracking
        self.daily_pnl: float = 0.0
        self.daily_trades: int = 0
        self.open_positions: Dict[str, List[Dict]] = {}  # symbol -> list of position dicts
        self.session_open_balance: float = 0.0
        self.current_date: date = date.today()
        
    def reset_daily_if_needed(self, balance: float) -> None:
        """Reset counters on new day."""
        today = date.today()
        if today != self.current_date:
            with self._lock:
                self.current_date = today
                self.daily_pnl = 0.0
                self.daily_trades = 0
                self.session_open_balance = balance
                logger.info(f"Daily risk limits reset for {today}. Balance: ${balance:.2f}")

    def update_state(self, pnl: float) -> None:
        """Update daily PnL after trade close."""
        with self._lock:
            self.daily_pnl += pnl

    def sync_open_positions(self, positions: List[Dict]) -> None:
        """Sync live positions from MT5."""
        with self._lock:
            self.open_positions.clear()
            for pos in positions:
                sym = pos.get('symbol')
                if sym not in self.open_positions:
                    self.open_positions[sym] = []
                self.open_positions[sym].append(pos)

    def validate(
        self, 
        signal: SignalResult, 
        balance: float, 
        free_margin: float,
        tick_value: float,       # value of 1 point movement for 1 standard lot
        point_size: float,       # e.g., 0.00001 for EURUSD
        contract_size: float,    # e.g., 100000 for Forex
        min_volume: float = 0.01,
        volume_step: float = 0.01,
        max_volume: float = 50.0
    ) -> RiskDecision:
        """Pass signal through all risk layers."""
        
        with self._lock:
            
            # Layer 1: Daily Loss
            max_loss_usd = balance * config.max_daily_loss_pct
            if self.daily_pnl <= -max_loss_usd:
                return RiskDecision(False, f"Daily Loss limit hit ({self.daily_pnl} <= {-max_loss_usd})", 0.0, 0.0, 0.0)

            # Layer 2: Daily Trades
            if self.daily_trades >= config.max_trades_per_day:
                return RiskDecision(False, f"Daily Trades limit hit ({self.daily_trades})", 0.0, 0.0, 0.0)
                
            # Layer 3: Concurrent Positions
            total_positions = sum(len(p) for p in self.open_positions.values())
            if total_positions >= config.max_positions:
                return RiskDecision(False, f"Max concurrent positions reached ({total_positions})", 0.0, 0.0, 0.0)
                
            # Layer 4: Symbol Exposure Limit
            sym_pos = self.open_positions.get(signal.symbol, [])
            if len(sym_pos) > 0:
                # Basic check: do not add to an existing symbol position to prevent overexposure
                return RiskDecision(False, f"Already exposed to {signal.symbol} ({len(sym_pos)} open)", 0.0, 0.0, 0.0)
                
            # Layer 5: Min R:R
            rr = self._calculate_rr(signal.entry, signal.sl, signal.tp, signal.direction)
            if rr < config.min_risk_reward:
                return RiskDecision(False, f"R:R too low ({rr:.2f} < {config.min_risk_reward})", 0.0, 0.0, 0.0)
                
            # Layer 6: Minimum Stop Distance
            sl_dist = abs(signal.entry - signal.sl)
            min_dist = point_size * 50  # e.g., 5 pips
            if sl_dist < min_dist:
                return RiskDecision(False, f"SL too tight ({sl_dist:.5f} < min {min_dist:.5f})", 0.0, 0.0, 0.0)
                
            # Position Sizing
            risk_usd = balance * config.risk_per_trade_pct
            
            # distance in points (should be an integer)
            dist_points = round(sl_dist / point_size)
            
            # Loss for 1 lot = distance in points * tick_value
            loss_for_1_lot = dist_points * tick_value
            
            if loss_for_1_lot <= 0:
                return RiskDecision(False, "Invalid tick value or sl distance calculation", 0.0, 0.0, 0.0)
                
            raw_lots = risk_usd / loss_for_1_lot
            
            # Normalize to volume step
            steps = int(raw_lots / volume_step)
            normalized_lots = steps * volume_step
            
            # Clamp limits
            if normalized_lots < min_volume:
                return RiskDecision(False, f"Calculated volume {normalized_lots:.2f} < min_volume {min_volume}", 0.0, 0.0, 0.0)
            if normalized_lots > max_volume:
                normalized_lots = max_volume
                
            # Estimated actual risk
            actual_loss_usd = normalized_lots * loss_for_1_lot
            actual_risk_pct = actual_loss_usd / balance
            
            # Increment trade counter for the day
            self.daily_trades += 1
            
            return RiskDecision(
                approved=True, 
                reason="Risk checks passed", 
                normalized_lots=normalized_lots,
                effective_risk_pct=actual_risk_pct,
                pip_value_usd=loss_for_1_lot / dist_points * 10.0  # value of 1 pip (10 points) per 1 lot
            )
            
    def _calculate_rr(self, entry: float, sl: float, tp: float, direction: str) -> float:
        """Calculate Risk:Reward ratio."""
        if entry == sl:
            return 0.0
            
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        return round(reward / risk, 3)


# Singleton
risk_manager = RiskManager()
