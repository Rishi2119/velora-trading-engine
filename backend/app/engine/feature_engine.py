"""
FeatureEngine: computes all technical indicators from OHLCV data.

Rules:
- Pure computation — zero MT5 calls, zero side effects
- Input: pandas DataFrame (columns: time, open, high, low, close, volume)
- Output: FeatureSet dataclass
- Caches last 10 results per symbol — never recomputes the same candle
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FeatureSet:
    symbol: str
    timeframe: str
    timestamp: pd.Timestamp         # candle close time
    close: float
    ema_fast: float                 # EMA(config.ema_fast, default 50)
    ema_slow: float                 # EMA(config.ema_slow, default 200)
    ema_spread_pct: float           # (ema_fast - ema_slow) / ema_slow * 100
    rsi: float                      # RSI(14), range [0, 100]
    atr: float                      # ATR(14) in price units
    atr_pct: float                  # ATR / close * 100
    adx: float                      # ADX(14), >= 0
    plus_di: float                  # +DI(14)
    minus_di: float                 # -DI(14)
    volatility_pct: float           # 20-bar rolling std / close * 100
    trend_direction: str            # "UP" | "DOWN" | "FLAT"
    bars_since_ema_cross: int       # bars since EMA fast crossed EMA slow


# ════════════════════════════════════════════════════════════════════════════════
# ENGINE
# ════════════════════════════════════════════════════════════════════════════════

class FeatureEngine:
    """
    Computes FeatureSet from OHLCV DataFrame.
    Results are cached per (symbol, last_candle_timestamp).
    """

    # Cache: symbol → list of (timestamp, FeatureSet)
    _cache: Dict[str, list] = {}
    _MAX_CACHE_PER_SYMBOL = 10

    def compute(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        ema_fast_period: int = 50,
        ema_slow_period: int = 200,
        rsi_period: int = 14,
    ) -> FeatureSet:
        """
        Compute FeatureSet from OHLCV DataFrame.

        Args:
            df: DataFrame with columns [time, open, high, low, close, volume]
                Must have at least 200 rows for reliable indicators.
            symbol: Trading symbol e.g. "EURUSD"
            timeframe: String e.g. "M15"
            ema_fast_period: Period for fast EMA  (default 50)
            ema_slow_period: Period for slow EMA  (default 200)
            rsi_period: RSI lookback period (default 14)

        Returns:
            FeatureSet (frozen dataclass)

        Raises:
            ValueError: if df has fewer than 50 rows or missing columns
        """
        required_cols = {"close", "high", "low"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"DataFrame missing columns: {required_cols - set(df.columns)}")
        if len(df) < 50:
            raise ValueError(f"Need at least 50 rows, got {len(df)}")

        # Cache key
        last_ts = pd.Timestamp(df.iloc[-1].get("time", df.index[-1]))
        cache_key = (symbol, last_ts)

        # Check cache
        for ts, feat in self._cache.get(symbol, []):
            if ts == last_ts:
                return feat

        # Compute
        result = self._compute(df, symbol, timeframe, ema_fast_period, ema_slow_period, rsi_period, last_ts)

        # Store in cache
        if symbol not in self._cache:
            self._cache[symbol] = []
        self._cache[symbol].append((last_ts, result))
        self._prune_cache(symbol)

        return result

    def _compute(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        ema_fast_period: int,
        ema_slow_period: int,
        rsi_period: int,
        timestamp: pd.Timestamp,
    ) -> FeatureSet:
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # ── EMA ──────────────────────────────────────────────────────────────
        ema_fast_s = self._ema(close, ema_fast_period)
        ema_slow_s = self._ema(close, ema_slow_period)

        ema_fast_val = float(ema_fast_s.iloc[-1])
        ema_slow_val = float(ema_slow_s.iloc[-1])
        ema_spread_pct = (
            (ema_fast_val - ema_slow_val) / abs(ema_slow_val) * 100
            if ema_slow_val != 0 else 0.0
        )

        # ── RSI ──────────────────────────────────────────────────────────────
        rsi_s = self._rsi(close, rsi_period)
        rsi_val = float(rsi_s.iloc[-1])
        rsi_val = max(0.0, min(100.0, rsi_val))  # Clamp to [0, 100]

        # ── ATR ──────────────────────────────────────────────────────────────
        atr_s = self._atr(high, low, close, 14)
        atr_val = float(atr_s.iloc[-1])
        close_val = float(close.iloc[-1])
        atr_pct = (atr_val / close_val * 100) if close_val != 0 else 0.0

        # ── ADX ──────────────────────────────────────────────────────────────
        adx_s, plus_di_s, minus_di_s = self._adx(high, low, close, 14)
        adx_val = float(adx_s.iloc[-1])
        plus_di_val = float(plus_di_s.iloc[-1])
        minus_di_val = float(minus_di_s.iloc[-1])
        # Guard NaN
        adx_val = 0.0 if np.isnan(adx_val) else adx_val
        plus_di_val = 0.0 if np.isnan(plus_di_val) else plus_di_val
        minus_di_val = 0.0 if np.isnan(minus_di_val) else minus_di_val

        # ── Volatility ────────────────────────────────────────────────────────
        vol_window = min(20, len(close))
        volatility_pct = (
            float(close.rolling(vol_window).std().iloc[-1]) / close_val * 100
            if close_val != 0 else 0.0
        )

        # ── Trend direction ───────────────────────────────────────────────────
        trend = self._trend(ema_fast_val, ema_slow_val)

        # ── Bars since EMA cross ──────────────────────────────────────────────
        bars_cross = self._bars_since_cross(ema_fast_s, ema_slow_s)

        return FeatureSet(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=timestamp,
            close=close_val,
            ema_fast=ema_fast_val,
            ema_slow=ema_slow_val,
            ema_spread_pct=ema_spread_pct,
            rsi=rsi_val,
            atr=atr_val,
            atr_pct=atr_pct,
            adx=adx_val,
            plus_di=plus_di_val,
            minus_di=minus_di_val,
            volatility_pct=volatility_pct,
            trend_direction=trend,
            bars_since_ema_cross=bars_cross,
        )

    # ── Indicator computation ─────────────────────────────────────────────────

    @staticmethod
    def _ema(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def _rsi(series: pd.Series, period: int) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, float("nan"))
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.ewm(com=period - 1, adjust=False).mean()

    @staticmethod
    def _adx(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate ADX, +DI, -DI."""
        prev_high = high.shift(1)
        prev_low = low.shift(1)
        prev_close = close.shift(1)

        # True Range
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Directional movement
        up_move = high - prev_high
        down_move = prev_low - low

        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

        # Smoothed
        atr_smooth = tr.ewm(com=period - 1, adjust=False).mean()
        plus_dm_smooth = plus_dm.ewm(com=period - 1, adjust=False).mean()
        minus_dm_smooth = minus_dm.ewm(com=period - 1, adjust=False).mean()

        plus_di = 100 * plus_dm_smooth / atr_smooth.replace(0, float("nan"))
        minus_di = 100 * minus_dm_smooth / atr_smooth.replace(0, float("nan"))

        # DX and ADX
        di_sum = (plus_di + minus_di).replace(0, float("nan"))
        dx = 100 * (plus_di - minus_di).abs() / di_sum
        adx = dx.ewm(com=period - 1, adjust=False).mean()

        return adx, plus_di, minus_di

    @staticmethod
    def _trend(ema_fast: float, ema_slow: float) -> str:
        spread_pct = (ema_fast - ema_slow) / abs(ema_slow) * 100 if ema_slow != 0 else 0.0
        if spread_pct > 0.05:
            return "UP"
        elif spread_pct < -0.05:
            return "DOWN"
        return "FLAT"

    @staticmethod
    def _bars_since_cross(ema_fast: pd.Series, ema_slow: pd.Series) -> int:
        """Return number of bars since last EMA crossover."""
        diff = ema_fast - ema_slow
        signs = diff.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        sign_change = signs.ne(signs.shift())
        cross_indexes = sign_change[sign_change].index.tolist()
        if not cross_indexes:
            return len(ema_fast)
        last_cross_pos = ema_fast.index.get_loc(cross_indexes[-1])
        return len(ema_fast) - 1 - last_cross_pos

    def _prune_cache(self, symbol: str) -> None:
        """Keep only the last MAX_CACHE_PER_SYMBOL entries per symbol."""
        if symbol in self._cache and len(self._cache[symbol]) > self._MAX_CACHE_PER_SYMBOL:
            self._cache[symbol] = self._cache[symbol][-self._MAX_CACHE_PER_SYMBOL:]


# Singleton instance for use across all modules
feature_engine = FeatureEngine()
