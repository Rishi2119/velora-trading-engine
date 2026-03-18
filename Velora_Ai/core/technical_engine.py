# // turbo
"""
Velora AI Engine — Full Technical Analysis Engine
Computes all signals needed by the 20-strategy dataset.
"""
import pandas as pd
import numpy as np
from loguru import logger


class TechnicalEngine:

    @staticmethod
    def compute_ema(df: pd.DataFrame, period: int) -> pd.Series:
        return df["Close"].ewm(span=period, adjust=False).mean()

    @staticmethod
    def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        delta = df["Close"].diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = -delta.clip(upper=0).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def compute_macd(df: pd.DataFrame, fast=12, slow=26, signal=9) -> dict:
        ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return {"macd": macd_line, "signal": signal_line, "histogram": histogram}

    @staticmethod
    def compute_bollinger(df: pd.DataFrame, period=20, std=2) -> dict:
        sma = df["Close"].rolling(period).mean()
        std_dev = df["Close"].rolling(period).std()
        return {"upper": sma + std * std_dev, "middle": sma, "lower": sma - std * std_dev}

    @staticmethod
    def compute_atr(df: pd.DataFrame, period=14) -> pd.Series:
        hl = df["High"] - df["Low"]
        hc = (df["High"] - df["Close"].shift()).abs()
        lc = (df["Low"] - df["Close"].shift()).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    @staticmethod
    def compute_stochastic(df: pd.DataFrame, k=14, d=3) -> dict:
        low_min = df["Low"].rolling(k).min()
        high_max = df["High"].rolling(k).max()
        k_line = 100 * (df["Close"] - low_min) / (high_max - low_min).replace(0, np.nan)
        d_line = k_line.rolling(d).mean()
        return {"k": k_line, "d": d_line}

    @staticmethod
    def compute_obv(df: pd.DataFrame) -> pd.Series:
        direction = np.sign(df["Close"].diff())
        return (direction * df["Volume"]).fillna(0).cumsum()

    @staticmethod
    def detect_pin_bar(df: pd.DataFrame) -> pd.Series:
        body = (df["Close"] - df["Open"]).abs()
        total = df["High"] - df["Low"]
        lower_wick = df[["Open", "Close"]].min(axis=1) - df["Low"]
        upper_wick = df["High"] - df[["Open", "Close"]].max(axis=1)
        bullish = (lower_wick >= 2 / 3 * total) & (total > 0)
        bearish = (upper_wick >= 2 / 3 * total) & (total > 0)
        result = pd.Series(0, index=df.index)
        result[bullish] = 1
        result[bearish] = -1
        return result

    @staticmethod
    def detect_engulfing(df: pd.DataFrame) -> pd.Series:
        prev_body_top = df[["Open", "Close"]].max(axis=1).shift(1)
        prev_body_bot = df[["Open", "Close"]].min(axis=1).shift(1)
        curr_body_top = df[["Open", "Close"]].max(axis=1)
        curr_body_bot = df[["Open", "Close"]].min(axis=1)
        bullish = (df["Close"] > df["Open"]) & (curr_body_top > prev_body_top) & (curr_body_bot < prev_body_bot) & (df["Close"].shift(1) < df["Open"].shift(1))
        bearish = (df["Close"] < df["Open"]) & (curr_body_top > prev_body_top) & (curr_body_bot < prev_body_bot) & (df["Close"].shift(1) > df["Open"].shift(1))
        result = pd.Series(0, index=df.index)
        result[bullish] = 1
        result[bearish] = -1
        return result

    @staticmethod
    def detect_rsi_divergence(df: pd.DataFrame, rsi: pd.Series, lookback=20) -> pd.Series:
        result = pd.Series(0, index=df.index)
        for i in range(lookback, len(df)):
            window_price = df["Close"].iloc[i-lookback:i]
            window_rsi = rsi.iloc[i-lookback:i]
            if window_price.iloc[-1] < window_price.min() + (window_price.max()-window_price.min())*0.1:
                if window_rsi.iloc[-1] > window_rsi.iloc[window_price.argmin()]:
                    result.iloc[i] = 1  # bullish divergence
            if window_price.iloc[-1] > window_price.max() - (window_price.max()-window_price.min())*0.1:
                if window_rsi.iloc[-1] < window_rsi.iloc[window_price.argmax()]:
                    result.iloc[i] = -1  # bearish divergence
        return result

    def compute_all(self, df: pd.DataFrame) -> dict:
        if df is None or len(df) < 50:
            return {}
        indicators = {}
        try:
            indicators["ema_8"]   = self.compute_ema(df, 8)
            indicators["ema_20"]  = self.compute_ema(df, 20)
            indicators["ema_50"]  = self.compute_ema(df, 50)
            indicators["ema_200"] = self.compute_ema(df, 200)
            indicators["rsi"]     = self.compute_rsi(df)
            indicators["macd"]    = self.compute_macd(df)
            indicators["bb"]      = self.compute_bollinger(df)
            indicators["atr"]     = self.compute_atr(df)
            indicators["stoch"]   = self.compute_stochastic(df)
            indicators["obv"]     = self.compute_obv(df)
            indicators["pin_bar"] = self.detect_pin_bar(df)
            indicators["engulfing"] = self.detect_engulfing(df)
            indicators["rsi_div"] = self.detect_rsi_divergence(df, indicators["rsi"])
        except Exception as e:
            logger.error(f"[TechnicalEngine] Compute error: {e}")
        return indicators

tech_engine = TechnicalEngine()
