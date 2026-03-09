def is_swing_high(df, idx, lookback=3):
    if idx < lookback or idx >= len(df) - lookback:
        return False
    high = df.iloc[idx]["high"]
    for i in range(1, lookback + 1):
        if high <= df.iloc[idx - i]["high"] or high <= df.iloc[idx + i]["high"]:
            return False
    return True


def is_swing_low(df, idx, lookback=3):
    if idx < lookback or idx >= len(df) - lookback:
        return False
    low = df.iloc[idx]["low"]
    for i in range(1, lookback + 1):
        if low >= df.iloc[idx - i]["low"] or low >= df.iloc[idx + i]["low"]:
            return False
    return True


def find_last_swing_high(df):
    for i in range(len(df) - 1, -1, -1):
        if is_swing_high(df, i):
            return df.iloc[i]["high"]
    return None


def find_last_swing_low(df):
    for i in range(len(df) - 1, -1, -1):
        if is_swing_low(df, i):
            return df.iloc[i]["low"]
    return None


def bullish_bos(df):
    high = find_last_swing_high(df)
    if high is None:
        return False, None
    return df.iloc[-1]["close"] > high, high


def bearish_bos(df):
    low = find_last_swing_low(df)
    if low is None:
        return False, None
    return df.iloc[-1]["close"] < low, low


def pullback_long(df):
    if len(df) < 2:
        return False
    prev, curr = df.iloc[-2], df.iloc[-1]
    return prev["close"] < prev["ema50"] and curr["close"] > curr["ema50"]


def pullback_short(df):
    if len(df) < 2:
        return False
    prev, curr = df.iloc[-2], df.iloc[-1]
    return prev["close"] > prev["ema50"] and curr["close"] < curr["ema50"]
