# rules.py
from config import RSI_RANGE, MIN_RR

def trend_rule(df):
    price = df["close"].iloc[-1]
    ema50 = df["ema50"].iloc[-1]
    ema200 = df["ema200"].iloc[-1]

    if ema50 > ema200 and price > ema50:
        return "BULLISH"
    elif ema50 < ema200 and price < ema50:
        return "BEARISH"
    else:
        return "NO_TREND"

def entry_rule(rsi_value):
    return RSI_RANGE[0] <= rsi_value <= RSI_RANGE[1]

def rr_rule(rr):
    return rr >= MIN_RR
