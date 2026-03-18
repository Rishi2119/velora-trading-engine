# // turbo
import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from pathlib import Path

DATA_PATH = Path("data/strategies.json")
OUTPUT_PATH = Path("data/processed_features.csv")

TIMEFRAME_ORDER = ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"]
COMPLEXITY_MAP = {1: "Beginner", 2: "Intermediate", 3: "Advanced"}
FALSE_SIGNAL_MAP = {"Low": 0, "Medium": 1, "High": 2}
SESSION_CATEGORIES = ["Asian", "London", "NY Session", "London + NY", "London Open", "Monday Open", "Any"]

def load_data():
    with open(DATA_PATH) as f:
        return pd.DataFrame(json.load(f))

def encode_timeframe(tf):
    try:
        return TIMEFRAME_ORDER.index(tf)
    except ValueError:
        return 3  # default H1

def encode_session(session):
    for i, s in enumerate(SESSION_CATEGORIES):
        if s in session:
            return i
    return len(SESSION_CATEGORIES) - 1

def preprocess(df):
    df["tf_encoded"] = df["primary_timeframe"].apply(encode_timeframe)
    df["session_encoded"] = df["session"].apply(encode_session)
    df["false_signal_encoded"] = df["false_signal_risk"].map(FALSE_SIGNAL_MAP).fillna(1)
    df["pairs_count"] = df["pairs"].apply(len)

    cat_dummies = pd.get_dummies(df["category"], prefix="cat")
    market_dummies = pd.get_dummies(df["market_condition"], prefix="mkt")
    df = pd.concat([df, cat_dummies, market_dummies], axis=1)

    numeric_cols = [
        "win_rate", "avg_rr", "profit_factor", "max_drawdown",
        "avg_holding_days", "min_capital", "risk_per_trade",
        "complexity", "num_indicators", "uses_volume",
        "confirmation_required", "pairs_count",
        "tf_encoded", "session_encoded", "false_signal_encoded"
    ]
    scaler = MinMaxScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"[Velora AI] Preprocessed {len(df)} strategies -> {OUTPUT_PATH}")
    return df

if __name__ == "__main__":
    df = load_data()
    preprocess(df)
