import os
import sys

# Ensure we can find the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
root_dir = os.path.abspath(os.path.join(parent_dir, ".."))

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if root_dir not in sys.path:
    sys.path.insert(1, root_dir)

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import joblib
import numpy as np
from pathlib import Path
import httpx
import json
from backend.config.settings import settings
from utils.logger import get_logger

log = get_logger("StrategyScoreAPI")

router = APIRouter()

# Note: We need absolute paths if running from a different directory
models_dir = Path(parent_dir) / "models"
clf = joblib.load(models_dir / "trend_classifier.pkl")
reg = joblib.load(models_dir / "winrate_regressor.pkl")

TIMEFRAME_ORDER = ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"]
SESSION_CATEGORIES = ["Asian", "London", "NY Session", "London + NY", "London Open", "Monday Open", "Any"]
FALSE_SIGNAL_MAP = {"Low": 0, "Medium": 1, "High": 2}

class StrategyInput(BaseModel):
    win_rate: float
    avg_rr: float
    profit_factor: float
    max_drawdown: float
    avg_holding_days: float
    complexity: int
    num_indicators: int
    uses_volume: int
    confirmation_required: int
    pairs_count: int
    primary_timeframe: str
    session: str
    false_signal_risk: str

class StrategyScore(BaseModel):
    is_trend_strategy: bool
    trend_probability: float
    predicted_win_rate: float
    profitability_score: float
    velora_rating: str
    ai_explanation: Optional[str] = None


def _get_ai_explanation(data: StrategyInput, rating: str, trend_prob: float, predicted_wr: float) -> str:
    """Uses OpenRouter (DeepSeek) to provide a localized rating explanation."""
    if not settings.OPENROUTER_API_KEY:
        return "AI Explanation unavailable: OPENROUTER_API_KEY not set."
        
    try:
        prompt = f"""
You are the Velora AI Trading Assistant. Analyze the following forex trading strategy and provide a concise 2-3 sentence explanation for its rating.

Strategy Metrics:
- Win Rate: {data.win_rate}
- Risk/Reward (Avg): {data.avg_rr}
- Profit Factor: {data.profit_factor}
- Max Drawdown: {data.max_drawdown}
- Hold Time: {data.avg_holding_days} days
- TF: {data.primary_timeframe} | Session: {data.session}

Velora Model Analysis:
- Velora Rating: {rating}
- Trend Probability: {trend_prob:.2%}
- Predicted True Win Rate: {predicted_wr:.2%}

Provide a short, professional, and analytical explanation on WHY it received this rating, and a brief recommendation.
"""
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": "You are an expert quantitative trading analyst."},
                {"role": "user", "content": prompt}
            ]
        }
        with httpx.Client(timeout=10.0) as client:
            res = client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.error(f"Failed to get AI explanation: {e}")
        return "Failed to fetch AI explanation."

@router.post("/api/strategy/score", response_model=StrategyScore)
def score_strategy(data: StrategyInput):
    tf = TIMEFRAME_ORDER.index(data.primary_timeframe) / len(TIMEFRAME_ORDER) if data.primary_timeframe in TIMEFRAME_ORDER else 0.5
    session = next((i for i, s in enumerate(SESSION_CATEGORIES) if s in data.session), len(SESSION_CATEGORIES) - 1)
    session = session / len(SESSION_CATEGORIES)
    false_signal = FALSE_SIGNAL_MAP.get(data.false_signal_risk, 1) / 2.0

    features = np.array([[
        data.win_rate, data.avg_rr, data.profit_factor, data.max_drawdown,
        data.avg_holding_days, data.complexity, data.num_indicators,
        data.uses_volume, data.confirmation_required, data.pairs_count,
        tf, session, false_signal
    ]])

    trend_prob = clf.predict_proba(features)[0][1]
    predicted_wr = float(reg.predict(features)[0])
    profitability = round(data.win_rate * data.avg_rr, 3)

    if profitability >= 1.8:
        rating = "ELITE"
    elif profitability >= 1.4:
        rating = "STRONG"
    elif profitability >= 1.0:
        rating = "MODERATE"
    else:
        rating = "WEAK — DO NOT TRADE"

    # Get AI explanation using DeepSeek
    explanation = _get_ai_explanation(data, rating, trend_prob, predicted_wr)

    return StrategyScore(
        is_trend_strategy=bool(trend_prob > 0.5),
        trend_probability=round(float(trend_prob), 3),
        predicted_win_rate=round(predicted_wr, 3),
        profitability_score=profitability,
        velora_rating=rating,
        ai_explanation=explanation
    )

