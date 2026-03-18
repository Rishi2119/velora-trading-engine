"""
Velora AI — Module 4 + Training Script: AI Decision Model
===========================================================
Trains a LightGBM / RandomForest / XGBoost classifier
on the Velora training dataset.

Usage:
    python train_model.py [--model lgbm|rf|xgb] [--data path/to/data.csv]

Output:
    models/velora_model.pkl
    models/velora_scaler.pkl
    models/velora_encoders.pkl
"""

import sys
import os
import argparse
import pickle
import warnings
import numpy as np
import pandas as pd

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier, VotingClassifier

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DATA_PATH, MODEL_PATH, SCALER_PATH, ENCODER_PATH
from utils.logger import get_logger

log = get_logger("ModelTrainer")

# Optional heavy libraries
try:
    import lightgbm as lgb
    LGBM_AVAILABLE = True
except ImportError:
    LGBM_AVAILABLE = False

try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE COLUMNS (must match dataset + FeatureExtractionEngine output)
# ─────────────────────────────────────────────────────────────────────────────

CATEGORICAL_FEATURES = ["trend_direction", "session", "strategy_type"]
BOOL_FEATURES        = ["structure_break", "liquidity_sweep", "pullback"]
NUMERIC_FEATURES     = ["momentum_strength", "volatility",
                         "support_resistance_strength", "spread"]
ALL_FEATURES         = CATEGORICAL_FEATURES + BOOL_FEATURES + NUMERIC_FEATURES
TARGET               = "action"


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING & PREPROCESSING
# ─────────────────────────────────────────────────────────────────────────────

def load_and_preprocess(data_path: str):
    """Load CSV, encode categoricals, return X, y, encoders, scaler."""
    df = pd.read_csv(data_path)
    log.info(f"Dataset loaded: {len(df)} rows | columns: {list(df.columns)}")
    log.info(f"Class distribution:\n{df[TARGET].value_counts()}")

    # ── Bool conversion ───────────────────────────────────────────────────────
    for col in BOOL_FEATURES:
        if df[col].dtype == object:
            df[col] = df[col].map({"True": 1, "False": 0, True: 1, False: 0})
        df[col] = df[col].astype(int)

    # ── Encode categoricals ───────────────────────────────────────────────────
    encoders = {}
    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    # ── Encode target ─────────────────────────────────────────────────────────
    target_le = LabelEncoder()
    df[TARGET] = target_le.fit_transform(df[TARGET])
    encoders[TARGET] = target_le

    X = df[ALL_FEATURES].values
    y = df[TARGET].values

    # ── Scale numerics (helps RF too) ─────────────────────────────────────────
    scaler = StandardScaler()
    # Only scale numeric columns; keep encoded categoricals as-is
    num_idx = [ALL_FEATURES.index(c) for c in NUMERIC_FEATURES]
    X[:, num_idx] = scaler.fit_transform(X[:, num_idx])

    return X, y, encoders, scaler


# ─────────────────────────────────────────────────────────────────────────────
# MODEL BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def build_rf():
    return RandomForestClassifier(
        n_estimators=300, max_depth=10, min_samples_leaf=4,
        class_weight="balanced", random_state=42, n_jobs=-1
    )

def build_lgbm(n_classes: int):
    if not LGBM_AVAILABLE:
        raise ImportError("lightgbm not installed. Run: pip install lightgbm")
    return lgb.LGBMClassifier(
        n_estimators=300, max_depth=8, learning_rate=0.05,
        num_leaves=31, class_weight="balanced",
        random_state=42, verbose=-1
    )

def build_xgb(n_classes: int):
    if not XGB_AVAILABLE:
        raise ImportError("xgboost not installed. Run: pip install xgboost")
    return XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        use_label_encoder=False, eval_metric="mlogloss",
        random_state=42, verbosity=0
    )

def build_ensemble(n_classes: int):
    """Soft voting ensemble of all available models."""
    estimators = [("rf", build_rf())]
    if LGBM_AVAILABLE:
        estimators.append(("lgbm", build_lgbm(n_classes)))
    if XGB_AVAILABLE:
        estimators.append(("xgb", build_xgb(n_classes)))
    log.info(f"Ensemble members: {[e[0] for e in estimators]}")
    return VotingClassifier(estimators=estimators, voting="soft")


# ─────────────────────────────────────────────────────────────────────────────
# TRAINING PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def train(model_type: str = "lgbm", data_path: str = DATA_PATH):
    os.makedirs("models", exist_ok=True)

    X, y, encoders, scaler = load_and_preprocess(data_path)
    n_classes = len(np.unique(y))
    log.info(f"Features shape: {X.shape} | Classes: {n_classes}")

    # ── Train/test split ──────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # ── Build model ───────────────────────────────────────────────────────────
    if model_type == "lgbm":
        model = build_lgbm(n_classes)
    elif model_type == "xgb":
        model = build_xgb(n_classes)
    elif model_type == "ensemble":
        model = build_ensemble(n_classes)
    else:
        model = build_rf()

    log.info(f"Training {model_type} model...")
    model.fit(X_train, y_train)

    # ── Evaluate ──────────────────────────────────────────────────────────────
    y_pred = model.predict(X_test)
    target_names = encoders[TARGET].classes_

    log.info("\n" + classification_report(y_test, y_pred, target_names=target_names))
    log.info(f"Confusion Matrix:\n{confusion_matrix(y_test, y_pred)}")

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X, y, cv=cv, scoring="f1_macro", n_jobs=-1)
    log.info(f"CV F1-macro: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # ── Save artefacts ────────────────────────────────────────────────────────
    with open(MODEL_PATH,   "wb") as f: pickle.dump(model,    f)
    with open(SCALER_PATH,  "wb") as f: pickle.dump(scaler,   f)
    with open(ENCODER_PATH, "wb") as f: pickle.dump(encoders, f)

    log.info(f"Model saved → {MODEL_PATH}")
    log.info(f"Scaler saved → {SCALER_PATH}")
    log.info(f"Encoders saved → {ENCODER_PATH}")
    return model, scaler, encoders


# ─────────────────────────────────────────────────────────────────────────────
# AI DECISION MODEL (inference wrapper)
# ─────────────────────────────────────────────────────────────────────────────

class AIDecisionModel:
    """
    Wraps the trained model for live inference.
    Loads saved pkl files and exposes a predict() method.
    """

    def __init__(self):
        self.model    = None
        self.scaler   = None
        self.encoders = None
        self._loaded  = False

    def load(self):
        """Load model artefacts from disk."""
        try:
            with open(MODEL_PATH,   "rb") as f: self.model    = pickle.load(f)
            with open(SCALER_PATH,  "rb") as f: self.scaler   = pickle.load(f)
            with open(ENCODER_PATH, "rb") as f: self.encoders = pickle.load(f)
            self._loaded = True
            log.info("AI model loaded successfully.")
        except FileNotFoundError:
            log.warning("Model files not found. Run train_model.py first.")
            self._loaded = False

    @property
    def is_ready(self) -> bool:
        return self._loaded

    def predict(self, features) -> dict:
        """
        Accepts a Features dataclass instance.
        Returns {"action": "BUY"|"SELL"|"NO_TRADE", "confidence": float}
        """
        if not self._loaded:
            return {"action": "NO_TRADE", "confidence": 0.0}

        try:
            X = self._features_to_array(features)
            proba = self.model.predict_proba(X)[0]
            idx   = int(np.argmax(proba))
            action_str = self.encoders[TARGET].inverse_transform([idx])[0]
            confidence = float(proba[idx])

            return {"action": action_str, "confidence": round(confidence, 4)}

        except Exception as e:
            log.error(f"Prediction error: {e}")
            return {"action": "NO_TRADE", "confidence": 0.0}

    def _features_to_array(self, features) -> np.ndarray:
        """Convert Features dataclass → numpy array in training column order."""
        from core.models import Features
        f = features

        # Categorical → encoded integers
        def encode(col, val):
            le = self.encoders.get(col)
            if le is None:
                return 0
            val_str = str(val)
            if val_str in le.classes_:
                return int(le.transform([val_str])[0])
            return 0   # unknown category → 0

        row = [
            encode("trend_direction", f.trend_direction),
            encode("session",         f.session),
            encode("strategy_type",   f.strategy_type),
            int(f.structure_break),
            int(f.liquidity_sweep),
            int(f.pullback),
            f.momentum_strength,
            f.volatility,
            f.support_resistance_strength,
            f.spread,
        ]

        X = np.array(row, dtype=float).reshape(1, -1)

        # Scale numeric columns
        num_idx = [ALL_FEATURES.index(c) for c in NUMERIC_FEATURES]
        X[:, num_idx] = self.scaler.transform(X[:, num_idx])

        return X


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the Velora AI model")
    parser.add_argument("--model", default="lgbm",
                        choices=["lgbm", "rf", "xgb", "ensemble"],
                        help="Model type to train")
    parser.add_argument("--data", default=DATA_PATH,
                        help="Path to training CSV")
    args = parser.parse_args()

    model, scaler, encoders = train(model_type=args.model, data_path=args.data)
    print("\n✅  Training complete. Model saved to models/")
