# // turbo
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
from config.settings import config


class StrategyLoader:
    def __init__(self):
        self.strategies = []
        self.classifier = None
        self.regressor = None
        self._load_strategies()
        self._load_models()

    def _load_strategies(self):
        try:
            with open(config.DATA_PATH) as f:
                self.strategies = json.load(f)
            logger.success(f"[StrategyLoader] Loaded {len(self.strategies)} strategies")
        except FileNotFoundError:
            logger.warning("[StrategyLoader] strategies.json not found — using empty dataset")
            self.strategies = []

    def _load_models(self):
        clf_path = config.MODELS_PATH / "trend_classifier.pkl"
        reg_path = config.MODELS_PATH / "winrate_regressor.pkl"
        try:
            if clf_path.exists():
                self.classifier = joblib.load(clf_path)
                logger.success("[StrategyLoader] Trend classifier loaded")
            if reg_path.exists():
                self.regressor = joblib.load(reg_path)
                logger.success("[StrategyLoader] Win rate regressor loaded")
        except Exception as e:
            logger.warning(f"[StrategyLoader] Model load failed: {e}")

    def get_strategies_for_regime(self, regime: str, session: str) -> list:
        SESSION_MAP = {
            "London": ["London", "London + NY", "London Open", "Any"],
            "NY Session": ["NY Session", "London + NY", "Any"],
            "Asian": ["Asian", "Any"],
            "Any": ["Any", "London", "NY Session", "London + NY"]
        }
        valid_sessions = SESSION_MAP.get(session, ["Any"])
        REGIME_MAP = {
            "trending_up": ["Trend Following", "Trend Continuation", "Multi-Timeframe"],
            "trending_down": ["Trend Following", "Trend Continuation", "Multi-Timeframe"],
            "ranging": ["Mean Reversion", "Support/Resistance", "Price Action"],
            "high_volatility": ["Breakout", "Price Action"],
            "low_volatility": ["Mean Reversion", "Price Action"],
            "reversal": ["Reversal", "Price Action"]
        }
        preferred_cats = REGIME_MAP.get(regime, ["Trend Following", "Price Action"])
        matches = [
            s for s in self.strategies
            if s.get("category") in preferred_cats
            and any(sess in s.get("session", "") for sess in valid_sessions)
            and s.get("profit_factor", 0) >= 1.4
        ]
        matches.sort(key=lambda x: x.get("profitability_score", 0), reverse=True)
        return matches[:5] if matches else self.strategies[:3]

    def get_strategy_by_id(self, sid: str) -> dict:
        return next((s for s in self.strategies if s["id"] == sid), {})

    def score_strategy(self, features: dict) -> dict:
        if self.regressor is None:
            return {"predicted_win_rate": 0.60, "is_trend": True}
        try:
            cols = ["win_rate","avg_rr","profit_factor","max_drawdown",
                    "avg_holding_days","complexity","num_indicators",
                    "uses_volume","confirmation_required","pairs_count"]
            X = np.array([[features.get(c, 0) for c in cols]])
            wr = float(self.regressor.predict(X)[0])
            trend = bool(self.classifier.predict(X)[0]) if self.classifier else True
            return {"predicted_win_rate": round(wr, 3), "is_trend": trend}
        except Exception as e:
            logger.warning(f"[StrategyLoader] Scoring error: {e}")
            return {"predicted_win_rate": 0.60, "is_trend": True}

strategy_loader = StrategyLoader()
