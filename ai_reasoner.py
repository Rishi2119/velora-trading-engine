def explain_decision(row, decision, rr):
    explanations = []
    score = 100

    # Trend
    if row["ema50"] > row["ema200"]:
        explanations.append("Trend: PASS (EMA50 above EMA200)")
    else:
        explanations.append("Trend: FAIL (EMA50 below EMA200)")
        score -= 40

    # RSI
    if 40 <= row["rsi"] <= 60:
        explanations.append(f"RSI: PASS ({round(row['rsi'],2)})")
    else:
        explanations.append(f"RSI: FAIL ({round(row['rsi'],2)})")
        score -= 30

    # RR
    if rr >= 2:
        explanations.append(f"RR: PASS ({rr})")
    else:
        explanations.append(f"RR: FAIL ({rr})")
        score -= 20

    score = max(score, 0)

    verdict = decision["decision"]

    return {
        "summary": explanations,
        "confidence": score,
        "verdict": verdict
    }
