"""
Velora AI — Module 2: Feature Extraction Engine
=================================================
Converts a MarketState into the Features vector
that matches the training dataset schema.
"""

import sys
from datetime import datetime, timezone

sys.path.insert(0, "..")
from config import SESSIONS
from core.models import MarketState, Features
from utils.logger import get_logger

log = get_logger("FeatureExtraction")


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE EXTRACTION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class FeatureExtractionEngine:
    """
    Converts raw MarketState → Features aligned with the training dataset.

    Feature definitions:
    ─────────────────────────────────────────────────────────────────────
    trend_direction             : bullish | bearish | sideways (EMA cross)
    structure_break             : True if price broke key swing high/low
    liquidity_sweep             : True if wick pierced swing extreme then reversed
    pullback                    : True if price retraced toward EMAs
    momentum_strength           : 0–1 normalised from RSI distance from 50
    volatility                  : 0–1 normalised ATR relative to price
    support_resistance_strength : 0–1 proximity to nearest S/R level
    session                     : Asia | London | NewYork
    spread                      : raw spread value
    strategy_type               : inferred by rule engine (set later)
    """

    # ── Thresholds ────────────────────────────────────────────────────────────
    EMA_SLOPE_PERIODS  = 5     # candles to check EMA slope
    PULLBACK_ATR_MULT  = 1.5   # how close price must be to EMA for pullback
    SWEEP_WICK_RATIO   = 0.35  # wick must be this fraction of candle range

    def __init__(self):
        pass

    def extract(self, state: MarketState, strategy_type: str = "intraday_momentum") -> Features:
        """
        Main entry point. Pass MarketState, get Features back.
        strategy_type is filled in by the Strategy Detection Engine.
        """
        try:
            trend  = self._trend_direction(state)
            sb     = self._structure_break(state)
            ls     = self._liquidity_sweep(state)
            pb     = self._pullback(state, trend)
            mom    = self._momentum_strength(state)
            vol    = self._volatility(state)
            sr     = self._sr_strength(state)
            sess   = self._session(state.timestamp)

            features = Features(
                trend_direction             = trend,
                structure_break             = sb,
                liquidity_sweep             = ls,
                pullback                    = pb,
                momentum_strength           = round(mom, 4),
                volatility                  = round(vol, 4),
                support_resistance_strength = round(sr, 4),
                session                     = sess,
                spread                      = round(state.spread, 4),
                strategy_type               = strategy_type,
            )
            log.debug(f"Features extracted: {features}")
            return features

        except Exception as e:
            log.error(f"Feature extraction failed: {e}")
            return Features()   # safe default

    # ── Individual feature methods ────────────────────────────────────────────

    def _trend_direction(self, s: MarketState) -> str:
        """EMA50 vs EMA200 cross + price position."""
        if s.ema_fast > s.ema_slow and s.close > s.ema_fast:
            return "bullish"
        elif s.ema_fast < s.ema_slow and s.close < s.ema_fast:
            return "bearish"
        else:
            return "sideways"

    def _structure_break(self, s: MarketState) -> bool:
        """
        BOS = price closed beyond recent swing high/low.
        We use a simple heuristic: close > swing_high or close < swing_low.
        """
        # Use 1% buffer to reduce noise
        buffer = s.close * 0.001
        broke_up   = s.close > (s.swing_high - buffer)
        broke_down = s.close < (s.swing_low + buffer)
        return bool(broke_up or broke_down)

    def _liquidity_sweep(self, s: MarketState) -> bool:
        """
        Liquidity sweep = wick pierces swing extreme but candle closes inside.
        Heuristic: wick-to-range ratio > threshold.
        """
        candle_range = s.high - s.low
        if candle_range < 1e-8:
            return False
        upper_wick = s.high  - max(s.open, s.close)
        lower_wick = min(s.open, s.close) - s.low
        wick_ratio = max(upper_wick, lower_wick) / candle_range
        # Also require the candle touches a swing extreme
        touches_extreme = (s.high >= s.swing_high * 0.998 or
                           s.low  <= s.swing_low  * 1.002)
        return bool(wick_ratio > self.SWEEP_WICK_RATIO and touches_extreme)

    def _pullback(self, s: MarketState, trend: str) -> bool:
        """
        Pullback = price retraced toward EMA zone but hasn't crossed it.
        """
        atr_zone = s.atr * self.PULLBACK_ATR_MULT
        if trend == "bullish":
            return bool(abs(s.close - s.ema_fast) < atr_zone and s.close > s.ema_slow)
        elif trend == "bearish":
            return bool(abs(s.close - s.ema_fast) < atr_zone and s.close < s.ema_slow)
        return False

    def _momentum_strength(self, s: MarketState) -> float:
        """Normalise RSI deviation from 50 into 0–1 range."""
        return min(abs(s.rsi - 50) / 50.0, 1.0)

    def _volatility(self, s: MarketState) -> float:
        """ATR as fraction of price, normalised to 0–1 scale."""
        raw = s.atr / (s.close + 1e-9)
        # Typical forex ATR/price ~0.001–0.010
        return min(raw / 0.01, 1.0)

    def _sr_strength(self, s: MarketState) -> float:
        """
        Proximity to swing high/low levels.
        Returns 1.0 when at level, 0.0 when far away.
        """
        dist_high = abs(s.close - s.swing_high)
        dist_low  = abs(s.close - s.swing_low)
        nearest   = min(dist_high, dist_low)
        range_    = (s.swing_high - s.swing_low) + 1e-9
        proximity = 1.0 - (nearest / range_)
        return max(0.0, min(1.0, proximity))

    def _session(self, ts: datetime) -> str:
        """Determine trading session from UTC hour."""
        try:
            if ts.tzinfo is None:
                hour = ts.hour
            else:
                hour = ts.astimezone(timezone.utc).hour

            # London overlaps NY — use priority order
            if 13 <= hour < 16:
                return "NewYork"   # overlap → treat as NY (highest volume)
            elif 7 <= hour < 16:
                return "London"
            elif 0 <= hour < 8:
                return "Asia"
            else:
                return "NewYork"   # 16-22 UTC still NY session
        except Exception:
            return "Asia"
