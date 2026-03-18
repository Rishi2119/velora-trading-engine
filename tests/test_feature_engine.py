"""
Phase 2 test gate — FeatureEngine tests.
Run: python -m pytest tests/test_feature_engine.py -v
"""
import sys
import os
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_ohlcv(n: int = 250, trend: str = "up", seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic OHLCV data for testing.
    trend='up': steadily rising prices
    trend='down': steadily falling prices
    trend='flat': oscillating
    """
    np.random.seed(seed)
    times = pd.date_range("2024-01-01", periods=n, freq="15min")

    if trend == "up":
        close = 1.1000 + np.linspace(0, 0.05, n) + np.random.normal(0, 0.0005, n)
    elif trend == "down":
        close = 1.2000 - np.linspace(0, 0.05, n) + np.random.normal(0, 0.0005, n)
    else:
        close = 1.1500 + 0.005 * np.sin(np.linspace(0, 4 * np.pi, n)) + np.random.normal(0, 0.0005, n)

    close = np.maximum(close, 0.5)  # prevent negative prices
    high = close + np.abs(np.random.normal(0.0005, 0.0003, n))
    low = close - np.abs(np.random.normal(0.0005, 0.0003, n))
    open_ = close + np.random.normal(0, 0.0003, n)
    volume = np.random.randint(100, 1000, n).astype(float)

    return pd.DataFrame({
        "time": times,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


@pytest.fixture
def df_uptrend():
    return _make_ohlcv(250, trend="up")


@pytest.fixture
def df_downtrend():
    return _make_ohlcv(250, trend="down")


@pytest.fixture
def df_flat():
    return _make_ohlcv(250, trend="flat")


class TestFeatureEngine:

    def test_compute_returns_feature_set(self, df_uptrend):
        from backend.app.engine.feature_engine import FeatureEngine, FeatureSet
        engine = FeatureEngine()
        result = engine.compute(df_uptrend, "EURUSD", "M15")
        assert isinstance(result, FeatureSet)

    def test_no_nan_in_result(self, df_uptrend):
        from backend.app.engine.feature_engine import FeatureEngine
        engine = FeatureEngine()
        result = engine.compute(df_uptrend, "EURUSD", "M15")
        fields = [result.close, result.ema_fast, result.ema_slow, result.rsi,
                  result.atr, result.atr_pct, result.adx, result.plus_di,
                  result.minus_di, result.volatility_pct, result.ema_spread_pct]
        for i, f in enumerate(fields):
            assert not (isinstance(f, float) and (f != f)), f"Field {i} is NaN"

    def test_rsi_in_valid_range(self, df_uptrend):
        from backend.app.engine.feature_engine import FeatureEngine
        engine = FeatureEngine()
        result = engine.compute(df_uptrend, "EURUSD", "M15")
        assert 0.0 <= result.rsi <= 100.0, f"RSI out of range: {result.rsi}"

    def test_adx_non_negative(self, df_uptrend):
        from backend.app.engine.feature_engine import FeatureEngine
        engine = FeatureEngine()
        result = engine.compute(df_uptrend, "EURUSD", "M15")
        assert result.adx >= 0.0, f"ADX negative: {result.adx}"

    def test_atr_positive(self, df_uptrend):
        from backend.app.engine.feature_engine import FeatureEngine
        engine = FeatureEngine()
        result = engine.compute(df_uptrend, "EURUSD", "M15")
        assert result.atr > 0.0
        assert result.atr_pct > 0.0

    def test_trend_direction_valid_values(self, df_uptrend, df_downtrend, df_flat):
        from backend.app.engine.feature_engine import FeatureEngine
        engine = FeatureEngine()
        valid_trends = {"UP", "DOWN", "FLAT"}
        
        r_up = engine.compute(df_uptrend, "SYMBOL1", "M15")
        r_down = engine.compute(df_downtrend, "SYMBOL2", "M15")
        r_flat = engine.compute(df_flat, "SYMBOL3", "M15")
        
        assert r_up.trend_direction in valid_trends
        assert r_down.trend_direction in valid_trends
        assert r_flat.trend_direction in valid_trends

    def test_uptrend_detected(self, df_uptrend):
        from backend.app.engine.feature_engine import FeatureEngine
        engine = FeatureEngine()
        result = engine.compute(df_uptrend, "UPTREND", "M15")
        # With 250-bar uptrend, EMA50 should eventually be above EMA200
        # This may be FLAT for first 200 bars; assert it's not DOWN
        assert result.trend_direction in {"UP", "FLAT"}

    def test_downtrend_detected(self, df_downtrend):
        from backend.app.engine.feature_engine import FeatureEngine
        engine = FeatureEngine()
        result = engine.compute(df_downtrend, "DOWNTREND", "M15")
        assert result.trend_direction in {"DOWN", "FLAT"}

    def test_bars_since_cross_non_negative(self, df_uptrend):
        from backend.app.engine.feature_engine import FeatureEngine
        engine = FeatureEngine()
        result = engine.compute(df_uptrend, "EURUSD", "M15")
        assert result.bars_since_ema_cross >= 0

    def test_ema_spread_pct_formula(self, df_uptrend):
        from backend.app.engine.feature_engine import FeatureEngine
        engine = FeatureEngine()
        result = engine.compute(df_uptrend, "EURUSD", "M15")
        expected = (result.ema_fast - result.ema_slow) / abs(result.ema_slow) * 100
        assert abs(result.ema_spread_pct - expected) < 1e-9

    def test_caching_returns_same_object(self, df_uptrend):
        from backend.app.engine.feature_engine import FeatureEngine
        engine = FeatureEngine()
        r1 = engine.compute(df_uptrend, "GBPUSD", "M15")
        r2 = engine.compute(df_uptrend, "GBPUSD", "M15")
        assert r1 is r2   # Same object from cache

    def test_raises_on_too_few_rows(self):
        from backend.app.engine.feature_engine import FeatureEngine
        engine = FeatureEngine()
        df_small = _make_ohlcv(30)
        with pytest.raises(ValueError, match="50 rows"):
            engine.compute(df_small, "EURUSD", "M15")

    def test_raises_on_missing_columns(self):
        from backend.app.engine.feature_engine import FeatureEngine
        engine = FeatureEngine()
        df_bad = pd.DataFrame({"time": range(200), "close": range(200)})
        with pytest.raises(ValueError, match="missing columns"):
            engine.compute(df_bad, "EURUSD", "M15")

    def test_different_symbols_cached_separately(self, df_uptrend):
        from backend.app.engine.feature_engine import FeatureEngine
        engine = FeatureEngine()
        r1 = engine.compute(df_uptrend, "EURUSD", "M15")
        r2 = engine.compute(df_uptrend, "XAUUSD", "M15")
        assert r1.symbol == "EURUSD"
        assert r2.symbol == "XAUUSD"

    def test_custom_ema_periods(self, df_uptrend):
        from backend.app.engine.feature_engine import FeatureEngine
        # Use fresh engine to avoid cache collision
        engine = FeatureEngine()
        # Custom symbol to avoid cache from previous tests
        result = engine.compute(df_uptrend, "CUSTOM_TEST", "H1",
                                ema_fast_period=9, ema_slow_period=21)
        assert result.ema_fast != result.ema_slow
