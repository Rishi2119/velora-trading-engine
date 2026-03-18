# // turbo
import pytest
import json
from pathlib import Path

def test_data_file_exists():
    assert Path("data/strategies.json").exists()

def test_data_has_20_strategies():
    with open("data/strategies.json") as f:
        data = json.load(f)
    assert len(data) == 20

def test_all_strategies_have_required_fields():
    required = ["id", "win_rate", "avg_rr", "profit_factor", "ai_label_trend", "ai_label_reversal"]
    with open("data/strategies.json") as f:
        data = json.load(f)
    for s in data:
        for field in required:
            assert field in s, f"Missing field {field} in {s.get('id')}"

def test_win_rates_are_realistic():
    with open("data/strategies.json") as f:
        data = json.load(f)
    for s in data:
        assert 0.40 <= s["win_rate"] <= 0.85, f"Unrealistic win rate in {s['id']}: {s['win_rate']}"

def test_profitability_scores():
    with open("data/strategies.json") as f:
        data = json.load(f)
    for s in data:
        score = s["win_rate"] * s["avg_rr"]
        assert score > 0, f"Zero profitability in {s['id']}"

def test_preprocess_runs():
    from ai.preprocess import load_data, preprocess
    df = load_data()
    processed = preprocess(df)
    assert len(processed) == 20

def test_models_can_train():
    from ai.train_model import train
    train()
    assert Path("models/trend_classifier.pkl").exists()
    assert Path("models/winrate_regressor.pkl").exists()
