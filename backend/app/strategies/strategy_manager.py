"""
Strategy Engine: Base strategy interface, implementations, and StrategyManager.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol
import logging

from backend.app.core.config import config
from backend.app.engine.feature_engine import FeatureSet
from backend.app.strategies.regime_detector import RegimeResult, MarketRegime

logger = logging.getLogger(__name__)


@dataclass
class SignalResult:
    strategy_name: str
    symbol: str
    direction: str          # "BUY" | "SELL" | "HOLD"
    confidence: float       # 0.0 to 100.0
    entry: float
    sl: float
    tp: float
    reason: str


class BaseStrategy(Protocol):
    """Protocol for all Velora trading strategies."""
    
    @property
    def name(self) -> str:
        ...
        
    def evaluate(self, features: FeatureSet, regime: RegimeResult) -> Optional[SignalResult]:
        """Return SignalResult if trading criteria met, else None."""
        ...


# ── Strategies ───────────────────────────────────────────────────────────────

class EmaRsiStrategy:
    """
    Ported from legacy rules.py and decision.py
    Trend following strategy using EMA cross and RSI pullbacks.
    """
    
    def __init__(self, rsi_min: int = 40, rsi_max: int = 60, min_rr: float = 3.0):
        self._name = "EmaRsi_Trend"
        self.rsi_min = rsi_min
        self.rsi_max = rsi_max
        self.min_rr = min_rr
        
    @property
    def name(self) -> str:
        return self._name
        
    def evaluate(self, features: FeatureSet, regime: RegimeResult) -> Optional[SignalResult]:
        # Only trade in trending regimes
        if regime.regime not in (MarketRegime.TREND_UP, MarketRegime.TREND_DOWN):
            return None
            
        # Long conditions
        if regime.regime == MarketRegime.TREND_UP:
            # Look for RSI pullback (not overbought yet)
            if self.rsi_min <= features.rsi <= self.rsi_max:
                # Calculate SL/TP
                entry = features.close
                sl = features.ema_slow  # SL below slow EMA
                sl_distance = entry - sl
                
                # Minimum viable stop
                if sl_distance < features.atr * 0.5:
                    sl = entry - (features.atr * 1.5)
                    sl_distance = entry - sl
                    
                tp = entry + (sl_distance * self.min_rr)
                
                return SignalResult(
                    strategy_name=self.name,
                    symbol=features.symbol,
                    direction="BUY",
                    confidence=regime.confidence * 0.8,
                    entry=entry,
                    sl=sl,
                    tp=tp,
                    reason=f"UPTREND + RSI pullback ({features.rsi:.1f})"
                )
                
        # Short conditions
        elif regime.regime == MarketRegime.TREND_DOWN:
            if self.rsi_min <= features.rsi <= self.rsi_max:
                entry = features.close
                sl = features.ema_slow  # SL above slow EMA
                sl_distance = sl - entry
                
                if sl_distance < features.atr * 0.5:
                    sl = entry + (features.atr * 1.5)
                    sl_distance = sl - entry
                    
                tp = entry - (sl_distance * self.min_rr)
                
                return SignalResult(
                    strategy_name=self.name,
                    symbol=features.symbol,
                    direction="SELL",
                    confidence=regime.confidence * 0.8,
                    entry=entry,
                    sl=sl,
                    tp=tp,
                    reason=f"DOWNTREND + RSI pullback ({features.rsi:.1f})"
                )
                
        return None


class BosStrategy:
    """
    Ported from legacy ai_reasoner.py
    Break of Structure strategy evaluating trend, momentum, and volatility.
    """
    
    def __init__(self, min_confidence: float = 70.0):
        self._name = "BOS_Momentum"
        self.min_confidence = min_confidence
        
    @property
    def name(self) -> str:
        return self._name
        
    def evaluate(self, features: FeatureSet, regime: RegimeResult) -> Optional[SignalResult]:
        # High volatility or low liquidity usually breaks structure logic
        if regime.regime in (MarketRegime.VOLATILE, MarketRegime.LOW_LIQUIDITY):
            return None
            
        score = 100.0
        reasons = []
        
        # Base direction from EMA cross
        direction = "BUY" if features.ema_fast > features.ema_slow else "SELL"
        
        # Penalties based on ai_reasoner.py logic
        
        # 1. Trend confirmation
        if direction == "BUY" and features.trend_direction != "UP":
            score -= 40
            reasons.append("EMA spreading but trend lacks strength")
        elif direction == "SELL" and features.trend_direction != "DOWN":
            score -= 40
            reasons.append("EMA spreading but trend lacks strength")
            
        # 2. RSI momentum
        if direction == "BUY" and features.rsi < 50:
            score -= 30
            reasons.append(f"RSI weak for BUY ({features.rsi:.1f})")
        elif direction == "SELL" and features.rsi > 50:
            score -= 30
            reasons.append(f"RSI weak for SELL ({features.rsi:.1f})")
            
        # 3. ADX strength
        if features.adx < 20:
            score -= 20
            reasons.append(f"ADX low ({features.adx:.1f})")
            
        score = max(0.0, score)
        
        if score >= self.min_confidence:
            entry = features.close
            
            # SL placed using ATR
            if direction == "BUY":
                sl = entry - (features.atr * 2.0)
                tp = entry + (features.atr * 2.0 * config.min_risk_reward)
            else:
                sl = entry + (features.atr * 2.0)
                tp = entry - (features.atr * 2.0 * config.min_risk_reward)
                
            summary = "; ".join(reasons) if reasons else "Strong momentum alignment"
            
            return SignalResult(
                strategy_name=self.name,
                symbol=features.symbol,
                direction=direction,
                confidence=score,
                entry=entry,
                sl=sl,
                tp=tp,
                reason=summary
            )
            
        return None


# ── Strategy Manager ─────────────────────────────────────────────────────────

class StrategyManager:
    """Loads and evaluates multiple strategies, returning the best signal."""
    
    def __init__(self):
        self.strategies: List[BaseStrategy] = [
            EmaRsiStrategy(min_rr=config.min_risk_reward),
            BosStrategy()
        ]
        
    def evaluate_all(self, features: FeatureSet, regime: RegimeResult) -> Optional[SignalResult]:
        """
        Evaluate all strategies. If multiple fire, pick the one with highest confidence.
        """
        signals = []
        for strategy in self.strategies:
            try:
                signal = strategy.evaluate(features, regime)
                if signal and signal.direction in ("BUY", "SELL"):
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Strategy {strategy.name} evaluation error: {e}")
                
        if not signals:
            return None
            
        # Return signal with highest confidence
        best_signal = max(signals, key=lambda s: s.confidence)
        
        if len(signals) > 1:
            logger.info(f"Multiple signals for {features.symbol}: chose {best_signal.strategy_name} (conf: {best_signal.confidence:.1f})")
            
        return best_signal


# Singleton
strategy_manager = StrategyManager()
