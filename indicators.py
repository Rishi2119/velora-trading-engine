import pandas as pd
import numpy as np


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute technical indicators and append them as new columns.

    Indicators added:
    - ema50 / ema200 — Exponential Moving Averages
    - rsi            — Relative Strength Index (14-period, NaN-safe)
    - atr            — Average True Range (14-period)
    - bb_upper / bb_middle / bb_lower — Bollinger Bands (20-period, 2σ)
    """
    close = df["close"]

    # ── EMA ──────────────────────────────────────────────────────────────────
    df["ema50"] = close.ewm(span=50, min_periods=50).mean()
    df["ema200"] = close.ewm(span=200, min_periods=200).mean()

    # ── RSI (14) ─────────────────────────────────────────────────────────────
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, min_periods=14).mean()
    avg_loss = loss.ewm(com=13, min_periods=14).mean()
    # Guard against divide-by-zero: when avg_loss == 0 RSI = 100
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    df["rsi"] = df["rsi"].fillna(100)  # all-gain periods → RSI = 100

    # ── ATR (14) ─────────────────────────────────────────────────────────────
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - close.shift()).abs()
    low_close = (df["low"] - close.shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = tr.ewm(com=13, min_periods=14).mean()

    # ── Bollinger Bands (20, 2σ) ──────────────────────────────────────────────
    bb_mid = close.rolling(20, min_periods=20).mean()
    bb_std = close.rolling(20, min_periods=20).std()
    df["bb_middle"] = bb_mid
    df["bb_upper"] = bb_mid + 2 * bb_std
    df["bb_lower"] = bb_mid - 2 * bb_std

    return df
