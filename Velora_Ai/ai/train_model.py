# // turbo
import json
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, mean_absolute_error
import joblib
from pathlib import Path

DATA_PATH = Path("data/processed_features.csv")
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

FEATURE_COLS = [
    "win_rate", "avg_rr", "profit_factor", "max_drawdown",
    "avg_holding_days", "complexity", "num_indicators",
    "uses_volume", "confirmation_required", "pairs_count",
    "tf_encoded", "session_encoded", "false_signal_encoded"
]

def train():
    df = pd.read_csv(DATA_PATH)
    available = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available]

    # --- Task 1: Trend vs Reversal Classifier ---
    y_trend = df["ai_label_trend"]
    clf = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(clf, X, y_trend, cv=cv, scoring="accuracy")
    clf.fit(X, y_trend)
    joblib.dump(clf, MODEL_DIR / "trend_classifier.pkl")
    print(f"[Velora AI] Trend Classifier CV Accuracy: {scores.mean():.2%} (+/- {scores.std():.2%})")

    # --- Task 2: Win Rate Regressor ---
    y_wr = df["win_rate"]
    reg = GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42)
    reg.fit(X, y_wr)
    joblib.dump(reg, MODEL_DIR / "winrate_regressor.pkl")
    print(f"[Velora AI] Win Rate Regressor trained. Features used: {available}")

    # --- Feature Importance ---
    importance = pd.Series(clf.feature_importances_, index=available).sort_values(ascending=False)
    print("\n[Velora AI] Top Features (Trend Classifier):")
    print(importance.head(8).to_string())

if __name__ == "__main__":
    train()
