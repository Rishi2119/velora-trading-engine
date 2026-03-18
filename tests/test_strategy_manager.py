"""
Phase 4 test gate — Strategy Engine tests.
Run: python -m pytest tests/test_strategy_manager.py -v
"""
import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.strategies.strategy_manager import StrategyManager, EmaRsiStrategy, BosStrategy
from backend.app.strategies.regime_detector import MarketRegime, RegimeResult
from backend.app.engine.feature_engine import FeatureSet


def _mock_features(**kwargs) -> FeatureSet:
    defaults = {
        "symbol": "EURUSD",
        "timeframe": "M15",
        "timestamp": pd.Timestamp("2024-01-01"),
        "close": 1.1000,
        "ema_fast": 1.1050,
        "ema_slow": 1.0950,
        "ema_spread_pct": 0.9,
        "rsi": 50.0,
        "atr": 0.0010,
        "atr_pct": 0.09,
        "adx": 30.0,
        "plus_di": 25.0,
        "minus_di": 15.0,
        "volatility_pct": 0.1,
        "trend_direction": "UP",
        "bars_since_ema_cross": 10,
    }
    defaults.update(kwargs)
    return FeatureSet(**defaults)


def _mock_regime(regime_type: str, conf: float = 80.0) -> RegimeResult:
    return RegimeResult(
        symbol="EURUSD",
        timeframe="M15",
        regime=regime_type,
        confidence=conf,
        adx_value=30.0,
        volatility=0.1,
        reason="Test"
    )


class TestEmaRsiStrategy:
    def test_no_trade_in_range(self):
        strat = EmaRsiStrategy()
        feat = _mock_features()
        reg = _mock_regime(MarketRegime.RANGE)
        assert strat.evaluate(feat, reg) is None

    def test_buy_in_uptrend_pullback(self):
        strat = EmaRsiStrategy(rsi_min=40, rsi_max=60)
        # RSI 50 is inside pullback zone
        feat = _mock_features(rsi=50.0, close=1.1000, ema_slow=1.0980)
        reg = _mock_regime(MarketRegime.TREND_UP, conf=90.0)
        
        signal = strat.evaluate(feat, reg)
        assert signal is not None
        assert signal.direction == "BUY"
        assert signal.strategy_name == "EmaRsi_Trend"
        assert signal.sl <= 1.0980  # SL placed below slow EMA

    def test_no_buy_if_overbought(self):
        strat = EmaRsiStrategy(rsi_max=60)
        feat = _mock_features(rsi=75.0)  # overbought, wait for pullback
        reg = _mock_regime(MarketRegime.TREND_UP)
        assert strat.evaluate(feat, reg) is None

    def test_sell_in_downtrend_pullback(self):
        strat = EmaRsiStrategy()
        feat = _mock_features(rsi=50.0, close=1.1000, ema_slow=1.1020, trend_direction="DOWN")
        reg = _mock_regime(MarketRegime.TREND_DOWN, conf=80.0)
        
        signal = strat.evaluate(feat, reg)
        assert signal is not None
        assert signal.direction == "SELL"
        assert signal.sl >= 1.1020  # SL above slow EMA


class TestBosStrategy:
    def test_no_trade_if_volatile(self):
        strat = BosStrategy()
        feat = _mock_features()
        reg = _mock_regime(MarketRegime.VOLATILE)
        assert strat.evaluate(feat, reg) is None
        
    def test_strong_buy_alignment(self):
        strat = BosStrategy(min_confidence=70.0)
        # Fast > Slow -> BUY bias. Trend=UP -> confirmed. RSI>50 -> confirmed. ADX>20 -> confirmed.
        feat = _mock_features(ema_fast=1.105, ema_slow=1.095, trend_direction="UP", rsi=60.0, adx=35.0)
        reg = _mock_regime(MarketRegime.TREND_UP)
        
        signal = strat.evaluate(feat, reg)
        assert signal is not None
        assert signal.direction == "BUY"
        assert signal.confidence == 100.0
        
    def test_weak_alignment_rejected(self):
        strat = BosStrategy(min_confidence=60.0)
        # Fast > Slow -> BUY bias. BUT trend is FLAT, RSI is weak, ADX is weak.
        feat = _mock_features(ema_fast=1.101, ema_slow=1.100, trend_direction="FLAT", rsi=40.0, adx=15.0)
        reg = _mock_regime(MarketRegime.RANGE)
        
        signal = strat.evaluate(feat, reg)
        assert signal is None  # Score drops below 60


class TestStrategyManager:
    def test_evaluates_all_returns_best(self):
        manager = StrategyManager()
        feat = _mock_features(rsi=50.0, ema_fast=1.105, ema_slow=1.095, trend_direction="UP", adx=30.0)
        reg = _mock_regime(MarketRegime.TREND_UP, conf=80.0)
        
        # EmaRsi will fire with conf = 80 * 0.8 = 64
        # BosStrategy will fire with conf = 100
        signal = manager.evaluate_all(feat, reg)
        
        assert signal is not None
        assert signal.strategy_name == "BOS_Momentum"
        assert signal.confidence == 100.0
