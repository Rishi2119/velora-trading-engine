def detect_regime(df):
    """
    Returns: (regime_name, trade_allowed, reason)
    """
    if len(df) < 50:
        return "UNKNOWN", False, "Not enough data"

    row = df.iloc[-1]

    # Volatility thresholds (relative)
    atr_series = df["atr"].dropna()
    if len(atr_series) < 20:
        return "UNKNOWN", False, "ATR not ready"

    atr_now = row["atr"]
    atr_low = atr_series.quantile(0.25)
    atr_high = atr_series.quantile(0.75)

    # Trend strength
    ema_distance = abs(row["ema50"] - row["ema200"])

    # 1) HIGH VOLATILITY (spikes)
    if atr_now > atr_high * 1.3:
        return "HIGH_VOLATILITY", False, "ATR spike"

    # 2) LOW VOLATILITY (dead)
    if atr_now < atr_low * 0.7:
        return "LOW_VOLATILITY", False, "Market too quiet"

    # 3) RANGING (no clear trend)
    if ema_distance < atr_now * 0.2:
        return "RANGING", False, "EMA compression"

    # 4) TRENDING (allowed)
    return "TRENDING", True, "Trend + healthy volatility"
