# // turbo
import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


# ─── CONFIG TESTS ─────────────────────────────────────────────────────────────
def test_config_loads():
    from config.settings import config
    assert config.MAX_RISK_PER_TRADE == 0.01
    assert config.MAX_DAILY_LOSS == 0.03
    assert config.MAX_DRAWDOWN == 0.10
    assert config.MAX_CONCURRENT_TRADES == 3

def test_strategy_data_exists():
    from config.settings import config
    assert config.DATA_PATH.exists(), "strategies.json must exist"
    with open(config.DATA_PATH) as f:
        data = json.load(f)
    assert len(data) == 20

def test_all_strategies_valid():
    from config.settings import config
    with open(config.DATA_PATH) as f:
        data = json.load(f)
    required = ["id","win_rate","avg_rr","profit_factor","category","ai_label_trend","ai_label_reversal"]
    for s in data:
        for field in required:
            assert field in s, f"Missing {field} in {s.get('id')}"
        assert 0.40 <= s["win_rate"] <= 0.85, f"Unrealistic win rate in {s['id']}"
        assert s["profit_factor"] > 0

# ─── TECHNICAL ENGINE TESTS ────────────────────────────────────────────────────
def test_technical_engine_computes():
    import pandas as pd
    import numpy as np
    from core.technical_engine import TechnicalEngine
    n = 100
    df = pd.DataFrame({
        "Open": np.random.uniform(1.08, 1.10, n),
        "High": np.random.uniform(1.09, 1.11, n),
        "Low":  np.random.uniform(1.07, 1.09, n),
        "Close":np.random.uniform(1.08, 1.10, n),
        "Volume": np.random.randint(100, 1000, n)
    })
    te = TechnicalEngine()
    result = te.compute_all(df)
    assert "ema_20" in result
    assert "rsi" in result
    assert "macd" in result
    assert "atr" in result
    assert not result["rsi"].iloc[-1] is None

# ─── RISK MANAGER TESTS ────────────────────────────────────────────────────────
def test_risk_allows_first_trade():
    from core.risk_manager import RiskManager
    rm = RiskManager()
    account = {"balance": 10000, "equity": 10000}
    result = rm.check_trade_allowed(account, [])
    assert result["allowed"] is True

def test_risk_blocks_max_trades():
    from core.risk_manager import RiskManager
    from config.settings import config
    rm = RiskManager()
    account = {"balance": 10000, "equity": 10000}
    fake_positions = [{"ticket": i} for i in range(config.MAX_CONCURRENT_TRADES)]
    result = rm.check_trade_allowed(account, fake_positions)
    assert result["allowed"] is False

def test_risk_blocks_daily_loss():
    from core.risk_manager import RiskManager
    rm = RiskManager()
    rm.record_trade_result(-350)  # 3.5% of 10000
    account = {"balance": 10000, "equity": 9650}
    result = rm.check_trade_allowed(account, [])
    assert result["allowed"] is False

def test_position_sizing():
    from core.risk_manager import RiskManager
    rm = RiskManager()
    lots = rm.calculate_position_size(10000, 20, 10.0, "EURUSD")
    assert 0.01 <= lots <= 10.0

def test_sl_tp_calculation():
    from core.risk_manager import RiskManager
    rm = RiskManager()
    result = rm.calculate_sl_tp(1.10000, "BUY", 0.0010, 5, rr=2.0)
    assert result["sl"] < 1.10000
    assert result["tp2"] > 1.10000
    assert result["rr"] == 2.0

# ─── STRATEGY LOADER TESTS ─────────────────────────────────────────────────────
def test_strategy_loader():
    from ai.strategy_loader import StrategyLoader
    sl = StrategyLoader()
    assert len(sl.strategies) == 20
    s = sl.get_strategy_by_id("S001")
    assert s["name"] == "EMA 20/50 Crossover Trend"

def test_strategies_for_regime():
    from ai.strategy_loader import StrategyLoader
    sl = StrategyLoader()
    results = sl.get_strategies_for_regime("trending_up", "London")
    assert len(results) > 0
    assert all(s.get("profit_factor", 0) >= 1.4 for s in results)

# ─── API TESTS ────────────────────────────────────────────────────────────────
def test_api_health():
    from fastapi.testclient import TestClient
    from api.main_api import app
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "online"

def test_api_strategies_endpoint():
    from fastapi.testclient import TestClient
    from api.main_api import app
    client = TestClient(app)
    resp = client.get("/api/strategies")
    assert resp.status_code == 200
    assert len(resp.json()) == 20

# ─── SIGNAL TESTS ─────────────────────────────────────────────────────────────
def test_signal_generator_no_crash():
    import pandas as pd
    import numpy as np
    from core.signal_generator import SignalGenerator
    n = 100
    df = pd.DataFrame({
        "Open": np.random.uniform(1.08, 1.10, n),
        "High": np.random.uniform(1.09, 1.11, n),
        "Low":  np.random.uniform(1.07, 1.09, n),
        "Close":np.random.uniform(1.08, 1.10, n),
        "Volume": np.random.randint(100, 1000, n)
    })
    sg = SignalGenerator()
    strategy = {"id": "S002", "category": "Trend + Momentum", "avg_rr": 2.2}
    result = sg.generate("EURUSD", df, strategy)
    assert "valid" in result
    assert "confluence" in result
