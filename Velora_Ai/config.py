"""
Velora AI Trading Engine — Configuration
"""

from dataclasses import dataclass, field
from typing import List, Dict

# ─────────────────────────────────────────────
# RISK MANAGEMENT
# ─────────────────────────────────────────────
RISK_PER_TRADE = 0.01          # 1% account risk
MAX_DAILY_LOSS = 0.03          # 3% max drawdown per day
MAX_OPEN_TRADES = 3
MIN_RR_RATIO = 2.0             # 1:2 minimum risk/reward

# ─────────────────────────────────────────────
# AI CONFIDENCE FILTER
# ─────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.65
HIGH_CONFIDENCE = 0.80

# ─────────────────────────────────────────────
# SPREAD / SLIPPAGE
# ─────────────────────────────────────────────
MAX_SPREAD_PIPS = 0.30         # reject trades above this spread
MAX_SLIPPAGE_PIPS = 3

# ─────────────────────────────────────────────
# INDICATORS
# ─────────────────────────────────────────────
EMA_FAST = 50
EMA_SLOW = 200
ATR_PERIOD = 14
RSI_PERIOD = 14
SWING_LOOKBACK = 20

# ─────────────────────────────────────────────
# TRADING PAIRS & TIMEFRAMES
# ─────────────────────────────────────────────
SYMBOLS = ["EURUSD", "GBPUSD", "BTCUSD"]
TIMEFRAME = "M15"              # primary timeframe
HTF_TIMEFRAME = "H1"          # higher timeframe for bias

# ─────────────────────────────────────────────
# SESSIONS (UTC)
# ─────────────────────────────────────────────
SESSIONS: Dict[str, tuple] = {
    "Asia":    (0, 8),
    "London":  (7, 16),
    "NewYork": (13, 22),
}

# ─────────────────────────────────────────────
# STRATEGY → REGIME MAPPING
# ─────────────────────────────────────────────
REGIME_STRATEGY_MAP: Dict[str, List[str]] = {
    "TRENDING":        ["pullback_trend", "structure_bos", "intraday_momentum"],
    "RANGING":         ["liquidity_reversal", "blackbox_trap"],
    "BREAKOUT":        ["breakout_retest"],
    "HIGH_VOLATILITY": ["blackbox_trap", "liquidity_reversal"],
}

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
DATA_PATH        = "data/training_dataset.csv"
MODEL_PATH       = "models/velora_model.pkl"
SCALER_PATH      = "models/velora_scaler.pkl"
ENCODER_PATH     = "models/velora_encoders.pkl"
LOG_PATH         = "logs/velora_trades.log"
JOURNAL_PATH     = "logs/trade_journal.csv"
