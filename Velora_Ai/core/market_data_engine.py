"""
Velora AI — Module 1: Market Data Engine
=========================================
Connects to MetaTrader 5, fetches candle data,
and computes technical indicators (EMA, ATR, RSI, swings).

Falls back to DEMO mode (synthetic data) if MT5 is not available.
"""

import sys
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Optional, List

sys.path.insert(0, "..")
from config import (EMA_FAST, EMA_SLOW, ATR_PERIOD, RSI_PERIOD,
                    SWING_LOOKBACK, TIMEFRAME)
from core.models import MarketState
from utils.logger import get_logger

log = get_logger("MarketDataEngine")

# ── Try importing MT5 ────────────────────────────────────────────────────────
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    log.warning("MetaTrader5 not installed — running in DEMO mode.")


# ─────────────────────────────────────────────────────────────────────────────
# INDICATOR HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _atr(high: pd.Series, low: pd.Series, close: pd.Series,
         period: int = ATR_PERIOD) -> pd.Series:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def _rsi(close: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    delta = close.diff()
    gain  = delta.clip(lower=0).ewm(span=period, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(span=period, adjust=False).mean()
    rs    = gain / (loss + 1e-9)
    return 100 - 100 / (1 + rs)


def _swing_high(high: pd.Series, lookback: int = SWING_LOOKBACK) -> float:
    return high.rolling(lookback).max().iloc[-1]


def _swing_low(low: pd.Series, lookback: int = SWING_LOOKBACK) -> float:
    return low.rolling(lookback).min().iloc[-1]


# ─────────────────────────────────────────────────────────────────────────────
# MARKET DATA ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class MarketDataEngine:
    """
    Fetches candles from MT5 (or synthetic demo data) and
    returns an enriched MarketState object.
    """

    TF_MAP = {
        "M1":  1,  "M5":  5,  "M15": 15, "M30": 30,
        "H1":  16388, "H4": 16390, "D1": 16408,
    }

    def __init__(self, symbol: str = "EURUSD", timeframe: str = TIMEFRAME,
                 n_candles: int = 250):
        self.symbol    = symbol
        self.timeframe = timeframe
        self.n_candles = n_candles
        self._connected = False

        if MT5_AVAILABLE:
            self._connected = self._connect()

    # ── MT5 connection ───────────────────────────────────────────────────────

    def _connect(self) -> bool:
        if not mt5.initialize():
            log.error(f"MT5 init failed: {mt5.last_error()}")
            return False
        log.info(f"MT5 connected — {mt5.terminal_info().name}")
        return True

    def shutdown(self):
        if MT5_AVAILABLE and self._connected:
            mt5.shutdown()

    # ── Public API ───────────────────────────────────────────────────────────

    def fetch(self) -> Optional[MarketState]:
        """
        Fetch latest candle data and compute all indicators.
        Returns the most recent MarketState.
        """
        df = self._fetch_candles()
        if df is None or len(df) < max(EMA_SLOW, SWING_LOOKBACK) + 10:
            log.warning("Insufficient candle data.")
            return None

        df = self._add_indicators(df)
        return self._to_market_state(df)

    def fetch_dataframe(self) -> Optional[pd.DataFrame]:
        """Return full candle DataFrame with indicators (useful for backtesting)."""
        df = self._fetch_candles()
        if df is None:
            return None
        return self._add_indicators(df)

    # ── Internal ─────────────────────────────────────────────────────────────

    def _fetch_candles(self) -> Optional[pd.DataFrame]:
        if MT5_AVAILABLE and self._connected:
            return self._fetch_mt5()
        return self._fetch_demo()

    def _fetch_mt5(self) -> Optional[pd.DataFrame]:
        tf_const = getattr(mt5, f"TIMEFRAME_{self.timeframe}", mt5.TIMEFRAME_M15)
        rates = mt5.copy_rates_from_pos(self.symbol, tf_const, 0, self.n_candles)
        if rates is None:
            log.error(f"Failed to fetch rates: {mt5.last_error()}")
            return None
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        df = df.rename(columns={"tick_volume": "volume"})
        return df[["time", "open", "high", "low", "close", "volume"]]

    def _fetch_demo(self) -> pd.DataFrame:
        """Generate realistic synthetic OHLCV data for demo/testing."""
        np.random.seed(42)
        n = self.n_candles
        close = 1.1000 + np.cumsum(np.random.normal(0, 0.0003, n))
        spread = 0.00010
        high   = close + np.abs(np.random.normal(0, 0.0005, n))
        low    = close - np.abs(np.random.normal(0, 0.0005, n))
        open_  = close + np.random.normal(0, 0.0002, n)
        times  = pd.date_range("2024-01-01", periods=n, freq="15min", tz="UTC")
        return pd.DataFrame({
            "time": times, "open": open_, "high": high,
            "low": low, "close": close, "volume": np.random.randint(100, 1000, n),
        })

    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["ema_fast"]  = _ema(df["close"], EMA_FAST)
        df["ema_slow"]  = _ema(df["close"], EMA_SLOW)
        df["atr"]       = _atr(df["high"], df["low"], df["close"])
        df["rsi"]       = _rsi(df["close"])
        df["swing_high"]= df["high"].rolling(SWING_LOOKBACK).max()
        df["swing_low"] = df["low"].rolling(SWING_LOOKBACK).min()

        # Estimate spread from OHLC (demo); use real spread from MT5 tick in production
        if "spread" not in df.columns:
            df["spread"] = (df["high"] - df["low"]) * 0.05
        return df.dropna().reset_index(drop=True)

    def _to_market_state(self, df: pd.DataFrame) -> MarketState:
        row = df.iloc[-1]
        return MarketState(
            symbol     = self.symbol,
            timestamp  = row["time"] if hasattr(row["time"], "to_pydatetime")
                         else datetime.utcnow(),
            open       = float(row["open"]),
            high       = float(row["high"]),
            low        = float(row["low"]),
            close      = float(row["close"]),
            volume     = float(row["volume"]),
            ema_fast   = float(row["ema_fast"]),
            ema_slow   = float(row["ema_slow"]),
            atr        = float(row["atr"]),
            rsi        = float(row["rsi"]),
            swing_high = float(row["swing_high"]),
            swing_low  = float(row["swing_low"]),
            spread     = float(row.get("spread", 0.0001)),
        )

    # ── Convenience ──────────────────────────────────────────────────────────

    def get_current_spread(self) -> float:
        if MT5_AVAILABLE and self._connected:
            info = mt5.symbol_info(self.symbol)
            return info.spread * info.point if info else 0.0
        return 0.0001  # demo default
