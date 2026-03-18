# // turbo
"""
Velora AI Engine — Signal Generator
Converts raw market data + indicators into structured trade signals.
"""
import pandas as pd
import numpy as np
from loguru import logger
from core.technical_engine import tech_engine
from typing import Optional


TIMEFRAME_ORDER = ["M1","M5","M15","M30","H1","H4","D1","W1"]


class SignalGenerator:

    def _get_session(self) -> str:
        from datetime import datetime, timezone
        hour = datetime.now(timezone.utc).hour
        if 7 <= hour < 10:   return "London Open"
        if 7 <= hour < 12:   return "London"
        if 12 <= hour < 16:  return "London + NY"
        if 16 <= hour < 21:  return "NY Session"
        return "Asian"

    def generate(self, symbol: str, df: pd.DataFrame, strategy: dict) -> dict:
        if df is None or len(df) < 50:
            return {"valid": False, "reason": "Insufficient data"}

        ind = tech_engine.compute_all(df)
        if not ind:
            return {"valid": False, "reason": "Indicator computation failed"}

        close = df["Close"].iloc[-1]
        prev_close = df["Close"].iloc[-2]

        ema20  = ind["ema_20"].iloc[-1]
        ema50  = ind["ema_50"].iloc[-1]
        ema200 = ind["ema_200"].iloc[-1]
        rsi    = ind["rsi"].iloc[-1]
        macd   = ind["macd"]["macd"].iloc[-1]
        macd_s = ind["macd"]["signal"].iloc[-1]
        macd_p = ind["macd"]["macd"].iloc[-2]
        macd_ps= ind["macd"]["signal"].iloc[-2]
        bb_u   = ind["bb"]["upper"].iloc[-1]
        bb_l   = ind["bb"]["lower"].iloc[-1]
        bb_m   = ind["bb"]["middle"].iloc[-1]
        atr    = ind["atr"].iloc[-1]
        stoch_k= ind["stoch"]["k"].iloc[-1]
        stoch_p= ind["stoch"]["k"].iloc[-2]
        pin    = ind["pin_bar"].iloc[-1]
        engulf = ind["engulfing"].iloc[-1]
        rsi_div= ind["rsi_div"].iloc[-1]
        obv    = ind["obv"].iloc[-1]
        obv_p  = ind["obv"].iloc[-2]

        cat = strategy.get("category", "")
        signal = {"valid": False, "direction": None, "confluence": 0, "symbol": symbol,
                  "close": close, "atr": atr, "strategy_id": strategy.get("id"),
                  "session": self._get_session()}

        score = 0

        # ─── Trend Following ───────────────────────────────────────────────
        if cat in ["Trend Following", "Trend Continuation", "Multi-Timeframe", "Trend Momentum"]:
            if close > ema200: score += 20
            if ema20 > ema50 and prev_close < ema20:
                signal["direction"] = "BUY"; score += 30
            elif ema20 < ema50 and prev_close > ema20:
                signal["direction"] = "SELL"; score += 30
            if signal["direction"] == "BUY" and rsi > 50:  score += 15
            if signal["direction"] == "SELL" and rsi < 50: score += 15
            if macd > macd_s and macd_p <= macd_ps:
                if signal["direction"] == "BUY": score += 15
            if macd < macd_s and macd_p >= macd_ps:
                if signal["direction"] == "SELL": score += 15
            if macd > 0 and signal["direction"] == "BUY": score += 10
            if macd < 0 and signal["direction"] == "SELL": score += 10

        # ─── Mean Reversion ────────────────────────────────────────────────
        elif cat == "Mean Reversion":
            if close <= bb_l and rsi < 35:
                signal["direction"] = "BUY"; score += 60
            elif close >= bb_u and rsi > 65:
                signal["direction"] = "SELL"; score += 60
            if engulf == 1 and signal["direction"] == "BUY": score += 20
            if engulf == -1 and signal["direction"] == "SELL": score += 20

        # ─── Reversal ──────────────────────────────────────────────────────
        elif cat in ["Reversal", "Price Action"]:
            if pin == 1 or engulf == 1: signal["direction"] = "BUY"; score += 50
            elif pin == -1 or engulf == -1: signal["direction"] = "SELL"; score += 50
            if rsi_div == 1 and signal["direction"] == "BUY":  score += 25
            if rsi_div == -1 and signal["direction"] == "SELL": score += 25
            if obv > obv_p and signal["direction"] == "BUY": score += 15
            if obv < obv_p and signal["direction"] == "SELL": score += 15

        # ─── Breakout ──────────────────────────────────────────────────────
        elif cat == "Breakout":
            recent_high = df["High"].iloc[-20:].max()
            recent_low  = df["Low"].iloc[-20:].min()
            if close > recent_high * 0.9995:
                signal["direction"] = "BUY"; score += 55
            elif close < recent_low * 1.0005:
                signal["direction"] = "SELL"; score += 55
            if atr > ind["atr"].rolling(20).mean().iloc[-1]: score += 20

        # ─── Oscillator Combo ──────────────────────────────────────────────
        elif cat == "Oscillator + Trend":
            if close > ema50 and stoch_k > stoch_p and stoch_p < 25:
                signal["direction"] = "BUY"; score += 60
            elif close < ema50 and stoch_k < stoch_p and stoch_p > 75:
                signal["direction"] = "SELL"; score += 60

        # ─── Minimum threshold ─────────────────────────────────────────────
        signal["confluence"] = min(score, 100)
        signal["valid"] = signal["direction"] is not None and score >= 55

        if not signal["valid"]:
            signal["reason"] = f"Confluence too low ({score}/100 < 55)"

        return signal

signal_generator = SignalGenerator()
