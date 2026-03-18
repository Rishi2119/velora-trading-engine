"""
Velora AI — Module 3 & 8: Strategy Detection + Market Regime Detector
=======================================================================
Analyses the Features vector to:
  1. Detect market regime (TRENDING / RANGING / BREAKOUT / HIGH_VOLATILITY)
  2. Select the best-fit strategy from the 6 known strategies
"""

import sys
from typing import Tuple

sys.path.insert(0, "..")
from config import REGIME_STRATEGY_MAP
from core.models import Features, Regime
from utils.logger import get_logger

log = get_logger("StrategyDetection")


# ─────────────────────────────────────────────────────────────────────────────
# MARKET REGIME DETECTOR (Module 8)
# ─────────────────────────────────────────────────────────────────────────────

class MarketRegimeDetector:
    """
    Determines market regime using:
    - trend_direction (from EMAs)
    - volatility level
    - structure_break flag
    - support_resistance_strength
    """

    # Thresholds
    HIGH_VOLATILITY_THRESHOLD = 0.70
    LOW_SR_THRESHOLD          = 0.35
    STRONG_TREND_MOMENTUM     = 0.55

    def detect(self, features: Features) -> Regime:
        vol   = features.volatility
        trend = features.trend_direction
        sb    = features.structure_break
        sr    = features.support_resistance_strength
        mom   = features.momentum_strength

        # High volatility overrides everything
        if vol > self.HIGH_VOLATILITY_THRESHOLD:
            regime = Regime.HIGH_VOLATILITY

        # Breakout: structure broken + moderate momentum
        elif sb and mom > 0.40:
            regime = Regime.BREAKOUT

        # Trending: clear directional bias + good momentum
        elif trend in ("bullish", "bearish") and mom > self.STRONG_TREND_MOMENTUM:
            regime = Regime.TRENDING

        # Ranging: sideways or weak momentum at SR levels
        else:
            regime = Regime.RANGING

        log.debug(f"Regime detected: {regime.value} | vol={vol:.2f} trend={trend} sb={sb}")
        return regime


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY DETECTION ENGINE (Module 3)
# ─────────────────────────────────────────────────────────────────────────────

class StrategyDetectionEngine:
    """
    Maps current Features + Regime → most appropriate strategy.

    Strategy rules (aligned with training data strategy_type column):
    ──────────────────────────────────────────────────────────────────
    structure_bos        : BOS confirmed + momentum + clear trend
    liquidity_reversal   : Liquidity sweep + reversal candle at SR
    breakout_retest      : Structure break + pullback to broken level
    pullback_trend       : Trending market + pullback to EMA zone
    blackbox_trap        : Fake breakout (structure_break + liq_sweep simultaneously)
    intraday_momentum    : Strong momentum during active session, no clear structure
    """

    def __init__(self):
        self.regime_detector = MarketRegimeDetector()

    def detect(self, features: Features) -> Tuple[str, Regime]:
        """
        Returns (strategy_type, regime).
        strategy_type is one of the 6 known strategies.
        """
        regime = self.regime_detector.detect(features)

        strategy = self._select_strategy(features, regime)
        log.info(f"Strategy: {strategy} | Regime: {regime.value}")

        # Update strategy_type in features (mutable)
        features.strategy_type = strategy
        return strategy, regime

    def _select_strategy(self, f: Features, regime: Regime) -> str:
        trend = f.trend_direction
        sb    = f.structure_break
        ls    = f.liquidity_sweep
        pb    = f.pullback
        mom   = f.momentum_strength
        sr    = f.support_resistance_strength

        # ── Blackbox Trap: fake-out = BOS + immediate liquidity sweep ─────────
        if sb and ls:
            return "blackbox_trap"

        # ── Structure BOS: clean break with momentum ──────────────────────────
        if sb and not ls and mom > 0.60 and trend in ("bullish", "bearish"):
            return "structure_bos"

        # ── Liquidity Reversal: sweep at SR, no confirmed BOS ─────────────────
        if ls and not sb and sr > 0.55:
            return "liquidity_reversal"

        # ── Breakout Retest: post-BOS pullback ────────────────────────────────
        if sb and pb and regime == Regime.BREAKOUT:
            return "breakout_retest"

        # ── Pullback in Trend: EMA pullback in trending regime ────────────────
        if pb and trend in ("bullish", "bearish") and regime == Regime.TRENDING:
            return "pullback_trend"

        # ── Intraday Momentum: catch-all for sessions with strong directional move
        return "intraday_momentum"
