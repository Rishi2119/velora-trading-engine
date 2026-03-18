"""
Velora AI — Core Data Models
Shared dataclasses used across all modules.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class Action(str, Enum):
    BUY      = "BUY"
    SELL     = "SELL"
    NO_TRADE = "NO_TRADE"


class Regime(str, Enum):
    TRENDING        = "TRENDING"
    RANGING         = "RANGING"
    BREAKOUT        = "BREAKOUT"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"


class Session(str, Enum):
    ASIA     = "Asia"
    LONDON   = "London"
    NEW_YORK = "NewYork"
    OFF      = "Off"


@dataclass
class MarketState:
    """Raw market data snapshot for one candle."""
    symbol:       str
    timestamp:    datetime
    open:         float
    high:         float
    low:          float
    close:        float
    volume:       float
    ema_fast:     float = 0.0   # EMA50
    ema_slow:     float = 0.0   # EMA200
    atr:          float = 0.0
    rsi:          float = 50.0
    swing_high:   float = 0.0
    swing_low:    float = 0.0
    spread:       float = 0.0


@dataclass
class Features:
    """Extracted feature vector aligned with training dataset."""
    trend_direction:             str   = "sideways"   # bullish | bearish | sideways
    structure_break:             bool  = False
    liquidity_sweep:             bool  = False
    pullback:                    bool  = False
    momentum_strength:           float = 0.5
    volatility:                  float = 0.5
    support_resistance_strength: float = 0.5
    session:                     str   = "Asia"
    spread:                      float = 0.1
    strategy_type:               str   = "intraday_momentum"


@dataclass
class Prediction:
    """AI model output."""
    action:     Action
    confidence: float
    strategy:   str
    regime:     Regime
    meta:       Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeSignal:
    """Fully qualified trade signal ready for execution."""
    symbol:      str
    action:      Action
    entry_price: float
    stop_loss:   float
    take_profit: float
    lot_size:    float
    confidence:  float
    strategy:    str
    timestamp:   datetime = field(default_factory=datetime.utcnow)
    ticket:      Optional[int] = None


@dataclass
class BacktestResult:
    """Summary metrics from a backtest run."""
    total_trades:   int
    wins:           int
    losses:         int
    win_rate:       float
    profit_factor:  float
    max_drawdown:   float
    sharpe_ratio:   float
    total_pnl:      float
    equity_curve:   list = field(default_factory=list)
