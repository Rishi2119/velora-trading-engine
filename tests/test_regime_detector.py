"""
Phase 3 test gate — RegimeDetector tests.
Run: python -m pytest tests/test_regime_detector.py -v
"""
import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.strategies.regime_detector import RegimeDetector, MarketRegime, RegimeResult
from backend.app.engine.feature_engine import FeatureSet


def _mock_feature_set(**kwargs) -> FeatureSet:
    """Helper to create a FeatureSet with defaults."""
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
        "adx": 20.0,
        "plus_di": 25.0,
        "minus_di": 15.0,
        "volatility_pct": 0.1,
        "trend_direction": "UP",
        "bars_since_ema_cross": 10,
    }
    defaults.update(kwargs)
    return FeatureSet(**defaults)


class TestRegimeDetector:

    def test_low_liquidity(self):
        detector = RegimeDetector()
        features = _mock_feature_set(volatility_pct=0.01)  # Below 0.02
        result = detector.classify(features)
        assert result.regime == MarketRegime.LOW_LIQUIDITY
        assert result.confidence == 100.0

    def test_volatile(self):
        detector = RegimeDetector()
        features = _mock_feature_set(volatility_pct=0.8)  # Above 0.5
        result = detector.classify(features)
        assert result.regime == MarketRegime.VOLATILE
        assert result.confidence == 80.0  # (0.8 / 0.5) * 50 = 80

    def test_trend_up(self):
        detector = RegimeDetector()
        features = _mock_feature_set(
            adx=30.0,
            plus_di=30.0,
            minus_di=10.0,
            trend_direction="UP",
            volatility_pct=0.2
        )
        result = detector.classify(features)
        assert result.regime == MarketRegime.TREND_UP

    def test_trend_down(self):
        detector = RegimeDetector()
        features = _mock_feature_set(
            adx=40.0,
            plus_di=10.0,
            minus_di=30.0,
            trend_direction="DOWN",
            volatility_pct=0.2
        )
        result = detector.classify(features)
        assert result.regime == MarketRegime.TREND_DOWN

    def test_trend_conflict_ema_down_di_up(self):
        detector = RegimeDetector()
        features = _mock_feature_set(
            adx=30.0,
            plus_di=30.0,
            minus_di=10.0,
            trend_direction="DOWN",  # Conflict!
            volatility_pct=0.2
        )
        result = detector.classify(features)
        assert result.regime == MarketRegime.TREND_DOWN  # Follows EMA trend on conflict
        assert result.confidence < 50.0  # Heavily penalized

    def test_ranging(self):
        detector = RegimeDetector()
        features = _mock_feature_set(
            adx=15.0,  # Below 25
            volatility_pct=0.2
        )
        result = detector.classify(features)
        assert result.regime == MarketRegime.RANGE
        assert result.confidence > 0
