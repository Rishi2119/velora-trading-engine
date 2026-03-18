"""
RegimeDetector: classifies current market conditions based on FeatureSet.
Zero MT5 calls, pure logic.
Output determines which strategies are allowed to execute.
"""
import logging
from dataclasses import dataclass
from typing import Dict, Any

from backend.app.engine.feature_engine import FeatureSet

logger = logging.getLogger(__name__)

# Regime Enums
class MarketRegime:
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    RANGE = "RANGE"
    VOLATILE = "VOLATILE"
    LOW_LIQUIDITY = "LOW_LIQUIDITY"


@dataclass(frozen=True)
class RegimeResult:
    symbol: str
    timeframe: str
    regime: str             # One of continuous strings above
    confidence: float       # 0.0 to 100.0
    adx_value: float
    volatility: float
    reason: str             # Human readable reason for the classification


class RegimeDetector:
    """Classifies the market regime for a specific FeatureSet."""

    def __init__(self, adx_threshold: int = 25, volatility_high_pct: float = 0.5, volatility_low_pct: float = 0.02):
        """
        Args:
            adx_threshold: Minimum ADX required to be considered a trending market.
            volatility_high_pct: If rolling std/close*100 > this, it's VOLATILE (dangerous).
            volatility_low_pct: If rolling std/close*100 < this, it's LOW_LIQUIDITY (dead).
        """
        self.adx_threshold = adx_threshold
        self.volatility_high_pct = volatility_high_pct
        self.volatility_low_pct = volatility_low_pct

    def classify(self, features: FeatureSet) -> RegimeResult:
        """Evaluate FeatureSet and return RegimeResult."""
        
        # 1. Check for extreme conditions first
        if features.volatility_pct < self.volatility_low_pct:
            return RegimeResult(
                symbol=features.symbol,
                timeframe=features.timeframe,
                regime=MarketRegime.LOW_LIQUIDITY,
                confidence=100.0,
                adx_value=features.adx,
                volatility=features.volatility_pct,
                reason=f"Volatility very low ({features.volatility_pct:.3f}% < {self.volatility_low_pct}%)",
            )
            
        if features.volatility_pct > self.volatility_high_pct:
            return RegimeResult(
                symbol=features.symbol,
                timeframe=features.timeframe,
                regime=MarketRegime.VOLATILE,
                confidence=min(100.0, (features.volatility_pct / self.volatility_high_pct) * 50),
                adx_value=features.adx,
                volatility=features.volatility_pct,
                reason=f"Volatility very high ({features.volatility_pct:.3f}% > {self.volatility_high_pct}%)",
            )
            
        # 2. Check for trending vs ranging using ADX and DIs
        if features.adx >= self.adx_threshold:
            # Trending
            # Use ADX difference to calculate confidence (maxes out at ADX=50)
            confidence = min(100.0, 50.0 + ((features.adx - self.adx_threshold) / 25.0) * 50.0)
            
            if features.plus_di > features.minus_di and features.trend_direction != "DOWN":
                regime = MarketRegime.TREND_UP
                reason = f"ADX >= {self.adx_threshold} ({features.adx:.1f}), +DI > -DI"
            elif features.minus_di > features.plus_di and features.trend_direction != "UP":
                regime = MarketRegime.TREND_DOWN
                reason = f"ADX >= {self.adx_threshold} ({features.adx:.1f}), -DI > +DI"
            else:
                # DIs are conflicting with EMA trend
                confidence = max(10.0, confidence - 30.0) # Penalty for conflict
                regime = MarketRegime.TREND_UP if features.trend_direction == "UP" else MarketRegime.TREND_DOWN
                reason = f"ADX >= {self.adx_threshold} but DIs conflict with EMAs"
                
            return RegimeResult(
                symbol=features.symbol,
                timeframe=features.timeframe,
                regime=regime,
                confidence=confidence,
                adx_value=features.adx,
                volatility=features.volatility_pct,
                reason=reason,
            )
            
        else:
            # Ranging
            # Confidence is higher when ADX is very low (e.g. 10 is stronger range than 20)
            range_strength = 1.0 - (features.adx / self.adx_threshold)
            confidence = max(20.0, min(100.0, range_strength * 100))
            
            return RegimeResult(
                symbol=features.symbol,
                timeframe=features.timeframe,
                regime=MarketRegime.RANGE,
                confidence=confidence,
                adx_value=features.adx,
                volatility=features.volatility_pct,
                reason=f"ADX < {self.adx_threshold} ({features.adx:.1f}) indicates no clear trend",
            )

# Singleton
regime_detector = RegimeDetector()
