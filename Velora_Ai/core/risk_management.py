"""
Velora AI — Module 5: Risk Management Engine
=============================================
Handles position sizing, SL/TP placement, and daily loss limits.
"""

import sys
from typing import Optional, Tuple

sys.path.insert(0, "..")
from config import (RISK_PER_TRADE, MAX_DAILY_LOSS, MAX_OPEN_TRADES,
                    MIN_RR_RATIO, MAX_SPREAD_PIPS)
from core.models import Action, MarketState, Features, TradeSignal
from utils.logger import get_logger

log = get_logger("RiskManagement")


class RiskManagementEngine:
    """
    Enforces institutional risk rules:
    - 1% risk per trade
    - 3% max daily loss
    - Max 3 simultaneous open trades
    - SL beyond structure / liquidity sweep
    - TP at minimum 1:2 RR
    """

    def __init__(self, account_balance: float = 10_000.0):
        self.account_balance = account_balance
        self.daily_pnl       = 0.0
        self.open_trades     = 0
        self._daily_reset_date = None

    # ── Daily reset ───────────────────────────────────────────────────────────

    def reset_daily(self):
        from datetime import date
        today = date.today()
        if self._daily_reset_date != today:
            self.daily_pnl = 0.0
            self._daily_reset_date = today
            log.info("Daily PnL counter reset.")

    # ── Pre-trade checks ──────────────────────────────────────────────────────

    def can_trade(self) -> Tuple[bool, str]:
        """
        Returns (allowed, reason). Enforces daily loss and open trade limits.
        """
        self.reset_daily()

        loss_pct = abs(self.daily_pnl) / max(self.account_balance, 1)
        if self.daily_pnl < 0 and loss_pct >= MAX_DAILY_LOSS:
            return False, f"Daily loss limit reached ({loss_pct*100:.1f}%)"

        if self.open_trades >= MAX_OPEN_TRADES:
            return False, f"Max open trades reached ({MAX_OPEN_TRADES})"

        return True, "OK"

    def spread_ok(self, spread: float) -> bool:
        return spread <= MAX_SPREAD_PIPS

    # ── Position sizing ───────────────────────────────────────────────────────

    def position_size(self, entry: float, stop_loss: float,
                      pip_value: float = 10.0) -> float:
        """
        Returns lot size based on 1% risk rule.

        pip_value : USD value of 1 pip for 1 standard lot (default = $10 for EURUSD)
        """
        sl_distance_price = abs(entry - stop_loss)
        if sl_distance_price < 1e-8:
            return 0.01  # minimum

        # Convert price distance to pips (assume 5-digit broker, 1 pip = 0.0001)
        sl_pips  = sl_distance_price / 0.0001
        risk_usd = self.account_balance * RISK_PER_TRADE
        lot_size = risk_usd / (sl_pips * pip_value)

        # Clip to broker limits
        lot_size = max(0.01, min(lot_size, 100.0))
        return round(lot_size, 2)

    # ── SL / TP placement ────────────────────────────────────────────────────

    def calculate_sl_tp(
        self,
        action: Action,
        entry:  float,
        state:  MarketState,
        features: Features,
    ) -> Tuple[float, float]:
        """
        Stop Loss: beyond swing high/low + 1 ATR buffer.
        Take Profit: minimum 1:2 RR from entry.
        """
        atr    = state.atr
        buffer = atr * 1.2

        if action == Action.BUY:
            # SL below swing low
            raw_sl  = state.swing_low - buffer
            sl_dist = entry - raw_sl
            stop_loss   = round(raw_sl, 5)
            take_profit = round(entry + sl_dist * MIN_RR_RATIO, 5)

        elif action == Action.SELL:
            # SL above swing high
            raw_sl  = state.swing_high + buffer
            sl_dist = raw_sl - entry
            stop_loss   = round(raw_sl, 5)
            take_profit = round(entry - sl_dist * MIN_RR_RATIO, 5)

        else:
            stop_loss   = entry
            take_profit = entry

        log.debug(f"SL={stop_loss:.5f} TP={take_profit:.5f} | ATR={atr:.5f}")
        return stop_loss, take_profit

    # ── Build trade signal ────────────────────────────────────────────────────

    def build_signal(
        self,
        action:     Action,
        state:      MarketState,
        features:   Features,
        confidence: float,
        strategy:   str,
    ) -> Optional[TradeSignal]:
        """
        Combines all checks and returns a validated TradeSignal (or None).
        """
        allowed, reason = self.can_trade()
        if not allowed:
            log.warning(f"Trade blocked: {reason}")
            return None

        if not self.spread_ok(features.spread):
            log.warning(f"Trade blocked: spread too wide ({features.spread})")
            return None

        entry = state.close
        sl, tp = self.calculate_sl_tp(action, entry, state, features)
        lots   = self.position_size(entry, sl)

        # Validate SL/TP make sense
        if action == Action.BUY and (sl >= entry or tp <= entry):
            log.warning("Invalid SL/TP for BUY — skipping.")
            return None
        if action == Action.SELL and (sl <= entry or tp >= entry):
            log.warning("Invalid SL/TP for SELL — skipping.")
            return None

        signal = TradeSignal(
            symbol      = state.symbol,
            action      = action,
            entry_price = round(entry, 5),
            stop_loss   = sl,
            take_profit = tp,
            lot_size    = lots,
            confidence  = confidence,
            strategy    = strategy,
        )
        log.info(f"Signal created: {signal}")
        return signal

    # ── Trade lifecycle callbacks ─────────────────────────────────────────────

    def on_trade_opened(self):
        self.open_trades += 1

    def on_trade_closed(self, pnl: float):
        self.open_trades = max(0, self.open_trades - 1)
        self.daily_pnl  += pnl
        log.info(f"Trade closed | PnL: {pnl:+.2f} | Daily PnL: {self.daily_pnl:+.2f}")

    def update_balance(self, new_balance: float):
        self.account_balance = new_balance
