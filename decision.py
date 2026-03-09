from config import RSI_RANGE, MIN_RR
from risk import calculate_rr

def make_decision(row, entry, stop, target, direction):
    reasons = []

    # Trend
    if direction == "LONG" and row["ema50"] <= row["ema200"]:
        reasons.append("EMA trend not bullish")
    if direction == "SHORT" and row["ema50"] >= row["ema200"]:
        reasons.append("EMA trend not bearish")

    # RSI filter
    if not (RSI_RANGE[0] <= row["rsi"] <= RSI_RANGE[1]):
        reasons.append("RSI not in range")

    rr = calculate_rr(entry, stop, target)
    if rr < MIN_RR:
        reasons.append(f"RR too low ({rr})")

    if reasons:
        return {"decision": "NO TRADE", "reasons": reasons, "rr": rr}

    return {
        "decision": "TRADE",
        "reasons": [f"{direction} structure + pullback aligned"],
        "rr": rr
    }
