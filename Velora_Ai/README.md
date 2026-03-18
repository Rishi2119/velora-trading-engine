# Velora AI Trading Engine

**Institutional-grade hybrid AI + rule-based trading agent**  
Built on your training dataset · Python · RandomForest / LightGBM / XGBoost · MT5

---

## Architecture

```
MarketDataEngine (MT5 / Demo)
    ↓  candles + indicators
FeatureExtractionEngine
    ↓  trend_direction, structure_break, liquidity_sweep, ...
StrategyDetectionEngine + MarketRegimeDetector
    ↓  strategy_type, regime (TRENDING/RANGING/BREAKOUT/HIGH_VOL)
AIDecisionModel  ←  trained on your 1,000-row dataset
    ↓  {"action": "BUY", "confidence": 0.83}
AI Confidence Filter  (threshold = 0.65)
    ↓  passes only high-confidence signals
RiskManagementEngine
    ↓  1% risk, SL/TP, max 3 trades, 3% daily loss limit
TradeExecutionEngine  →  MT5 (or paper trade)
    ↓  ticket number
Trade Journal (logs/trade_journal.csv)
```

---

## Folder Structure

```
velora_ai/
├── config.py                        # All constants and thresholds
├── velora_engine.py                 # Main orchestrator / inference loop
├── train_model.py                   # Model training + AIDecisionModel class
├── api.py                           # FastAPI REST layer (optional)
├── requirements.txt
│
├── core/
│   ├── models.py                    # Shared dataclasses (MarketState, Features, etc.)
│   ├── market_data_engine.py        # Module 1: MT5 data + indicators
│   ├── feature_extraction.py        # Module 2: Features from MarketState
│   ├── strategy_detection.py        # Module 3 + 8: Strategy + Regime detector
│   ├── risk_management.py           # Module 5: Position sizing, SL/TP, limits
│   └── execution_engine.py          # Module 6: MT5 execution + paper trade
│
├── backtesting/
│   └── backtest_engine.py           # Module 9: Backtest + metrics
│
├── data/
│   └── training_dataset.csv         # Your 1,000-row Velora dataset
│
├── models/                          # Saved after training
│   ├── velora_model.pkl
│   ├── velora_scaler.pkl
│   └── velora_encoders.pkl
│
├── logs/
│   ├── velora_trades.log
│   └── trade_journal.csv
│
└── utils/
    └── logger.py
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Train the model

```bash
# RandomForest (no extra deps)
python train_model.py --model rf

# LightGBM (recommended — install lightgbm first)
python train_model.py --model lgbm

# XGBoost
python train_model.py --model xgb

# Soft-voting ensemble of all available
python train_model.py --model ensemble
```

Training output (RandomForest on your dataset):
```
CV F1-macro: 0.9975 ± 0.0050
Accuracy:    100% on test set
```

### 3. Run a single inference cycle

```bash
python velora_engine.py --symbol EURUSD --once
```

### 4. Start the live loop (paper trade mode without MT5)

```bash
python velora_engine.py --symbol EURUSD --interval 60
```

### 5. Run the backtester

```bash
python backtesting/backtest_engine.py
```

### 6. Start the REST API

```bash
pip install fastapi uvicorn
uvicorn api:app --host 0.0.0.0 --port 8000
```

API docs: `http://localhost:8000/docs`

---

## Inference Loop

```python
from velora_engine import VeloraEngine

engine = VeloraEngine(symbol="EURUSD", confidence_threshold=0.65)

# Single cycle
result = engine.run_once()
# {"action": "BUY", "confidence": 0.83, "strategy": "structure_bos", "regime": "TRENDING", ...}

# Live loop (blocks until Ctrl+C)
engine.run(interval_seconds=60)
```

---

## Module Summary

| # | Module | File | Purpose |
|---|--------|------|---------|
| 1 | Market Data Engine | `core/market_data_engine.py` | Candles + EMA50/200 + ATR + RSI + Swings |
| 2 | Feature Extraction | `core/feature_extraction.py` | MarketState → 10-feature vector |
| 3 | Strategy Detection | `core/strategy_detection.py` | Detects 1 of 6 strategies |
| 4 | AI Decision Model | `train_model.py` | RF/LGBM/XGB → BUY/SELL/NO_TRADE + confidence |
| 5 | Risk Management | `core/risk_management.py` | 1% risk, SL/TP, daily loss limit |
| 6 | Trade Execution | `core/execution_engine.py` | MT5 order send + paper trade fallback |
| 7 | Confidence Filter | `velora_engine.py` | Blocks trades below 0.65 confidence |
| 8 | Regime Detector | `core/strategy_detection.py` | TRENDING / RANGING / BREAKOUT / HIGH_VOL |
| 9 | Backtester | `backtesting/backtest_engine.py` | Win rate, profit factor, Sharpe, drawdown |

---

## Strategies

| Strategy | Trigger Conditions |
|----------|--------------------|
| `structure_bos` | BOS confirmed + momentum > 0.60 + clear trend |
| `liquidity_reversal` | Liquidity sweep + SR strength > 0.55 |
| `breakout_retest` | BOS + pullback in BREAKOUT regime |
| `pullback_trend` | EMA pullback in TRENDING regime |
| `blackbox_trap` | BOS + liquidity sweep simultaneously (fake-out) |
| `intraday_momentum` | Catch-all: strong momentum in active session |

---

## Risk Rules

| Rule | Value |
|------|-------|
| Risk per trade | 1% of balance |
| Max daily loss | 3% of balance |
| Max open trades | 3 |
| Min risk/reward | 1:2 |
| Max spread | 0.30 pips |
| Stop loss | Beyond swing high/low + 1.2× ATR buffer |

---

## MT5 Integration

The engine auto-detects MT5. If MT5 is installed and initialised, it uses live data and live execution. If not, it runs in **DEMO mode** (synthetic data + paper trades).

To connect MT5:
1. Install MetaTrader5: `pip install MetaTrader5`
2. Open MT5 terminal and enable `Tools → Options → Expert Advisors → Allow algorithmic trading`
3. Run `velora_engine.py` — it will auto-connect

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/status` | Engine health + account info |
| POST | `/signal` | Run one inference cycle |
| GET | `/positions` | Open positions |
| POST | `/close/{ticket}` | Close a specific trade |
| POST | `/kill_switch` | Close ALL trades immediately |
| POST | `/train` | Retrain model (background) |
| POST | `/backtest` | Run backtest + return metrics |
| GET | `/journal` | Recent trade journal |

---

## Extending the System

**Swap the model:**
```python
# In train_model.py — add any sklearn-compatible model:
from sklearn.ensemble import GradientBoostingClassifier
model = GradientBoostingClassifier(...)
```

**Add a new strategy:**
```python
# In core/strategy_detection.py → _select_strategy():
if my_condition(f):
    return "my_new_strategy"
```

**Change risk parameters:**
```python
# In config.py:
RISK_PER_TRADE = 0.005   # 0.5%
CONFIDENCE_THRESHOLD = 0.70
```

**Multi-symbol loop:**
```python
for symbol in ["EURUSD", "GBPUSD", "BTCUSD"]:
    engine = VeloraEngine(symbol=symbol)
    engine.run_once()
```

---

*Velora AI Trading Engine — designed for integration into the Velora Trading Terminal*
