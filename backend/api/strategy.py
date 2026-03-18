"""
Backend API — Strategy Configuration
GET  /api/v1/strategy/config       — current running strategy config
POST /api/v1/strategy/config       — hot-update config (no engine restart)
GET  /api/v1/strategy/filters      — filter gate status snapshot
POST /api/v1/strategy/backtest     — trigger quick candle signal replay
"""
import os
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from backend.utils.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/strategy", tags=["Strategy"])

_CONFIG_OVERRIDE_PATH = "logs/strategy_override.json"


# ── Schema ────────────────────────────────────────────────────────────────────

class StrategyConfig(BaseModel):
    # Risk
    risk_per_trade_pct: float = Field(default=1.0, ge=0.1, le=2.0,
                                      description="Risk % per trade (0.1-2.0)")
    min_rr: float = Field(default=3.0, ge=1.5, le=10.0)
    max_daily_trades: int = Field(default=5, ge=1, le=20)
    max_concurrent: int = Field(default=3, ge=1, le=10)
    max_spread_pips: float = Field(default=3.0, ge=0.5, le=10.0)
    circuit_breaker_pct: float = Field(default=5.0, ge=1.0, le=20.0,
                                       description="Circuit breaker drawdown % (1-20)")

    # Indicators
    ema_fast: int = Field(default=50, ge=5, le=200)
    ema_slow: int = Field(default=200, ge=50, le=500)
    rsi_period: int = Field(default=14, ge=5, le=50)
    atr_period: int = Field(default=14, ge=5, le=50)

    # Filters
    enable_session_filter: bool = True
    enable_news_filter: bool = True
    enable_spread_filter: bool = True
    news_buffer_minutes: int = Field(default=15, ge=5, le=60)

    # Pairs
    pairs: str = Field(default="EURUSD", description="Comma-separated pair list")
    timeframe: str = Field(default="M15")


def _load_config() -> dict:
    """Load base config from engine and merge any saved overrides."""
    try:
        import config as cfg
        base = {
            "risk_per_trade_pct": cfg.RISK_PER_TRADE * 100,
            "min_rr": cfg.MIN_RISK_REWARD,
            "max_daily_trades": cfg.MAX_DAILY_TRADES,
            "max_concurrent": cfg.MAX_CONCURRENT_TRADES,
            "max_spread_pips": cfg.MAX_SPREAD_PIPS,
            "circuit_breaker_pct": cfg.CIRCUIT_BREAKER_PCT * 100,
            "ema_fast": cfg.EMA_FAST,
            "ema_slow": cfg.EMA_SLOW,
            "rsi_period": cfg.RSI_PERIOD,
            "atr_period": cfg.ATR_PERIOD,
            "enable_session_filter": cfg.ENABLE_SESSION_FILTER,
            "enable_news_filter": cfg.ENABLE_NEWS_FILTER,
            "enable_spread_filter": cfg.ENABLE_SPREAD_FILTER,
            "news_buffer_minutes": cfg.NEWS_BUFFER_MINUTES,
            "pairs": ",".join(cfg.PAIRS),
            "timeframe": cfg.TIMEFRAME,
        }
    except Exception as e:
        logger.warning(f"Could not load engine config: {e}")
        base = {}

    # Apply saved overrides
    if os.path.exists(_CONFIG_OVERRIDE_PATH):
        try:
            with open(_CONFIG_OVERRIDE_PATH) as f:
                overrides = json.load(f)
            base.update(overrides)
        except Exception:
            pass

    return base


def _save_override(data: dict) -> None:
    """Persist config override for next engine restart."""
    os.makedirs("logs", exist_ok=True)
    with open(_CONFIG_OVERRIDE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _apply_hot_reload(data: dict) -> None:
    """Apply config changes to live engine modules without restart."""
    try:
        import config as cfg
        if "risk_per_trade_pct" in data:
            cfg.RISK_PER_TRADE = data["risk_per_trade_pct"] / 100
        if "min_rr" in data:
            cfg.MIN_RISK_REWARD = data["min_rr"]
        if "max_daily_trades" in data:
            cfg.MAX_DAILY_TRADES = int(data["max_daily_trades"])
        if "max_concurrent" in data:
            cfg.MAX_CONCURRENT_TRADES = int(data["max_concurrent"])
        if "max_spread_pips" in data:
            cfg.MAX_SPREAD_PIPS = float(data["max_spread_pips"])
        if "enable_session_filter" in data:
            cfg.ENABLE_SESSION_FILTER = bool(data["enable_session_filter"])
        if "enable_news_filter" in data:
            cfg.ENABLE_NEWS_FILTER = bool(data["enable_news_filter"])
        logger.info("Hot-reloaded strategy config")
    except Exception as e:
        logger.warning(f"Hot-reload partial failure: {e}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/config")
async def get_strategy_config():
    """Return current strategy configuration."""
    return {"config": _load_config(), "override_file": _CONFIG_OVERRIDE_PATH}


@router.post("/config")
async def update_strategy_config(body: StrategyConfig,
                                  current: dict = Depends(get_current_user)):
    """
    Hot-update strategy config.
    Changes take effect on next loop iteration without engine restart.
    """
    data = body.dict()
    _apply_hot_reload(data)
    _save_override(data)
    return {"success": True, "config": data, "message": "Config updated — no restart needed"}


@router.get("/filters")
async def get_filter_status():
    """Current filter gate status snapshot."""
    result = {}

    try:
        from session_filter import get_session_info, is_trading_session
        result["session"] = get_session_info()
        result["session"]["is_open"] = is_trading_session()
    except Exception as e:
        result["session"] = {"error": str(e)}

    try:
        from news_filter import is_news_blackout
        result["news"] = {"blocked": is_news_blackout()}
    except Exception as e:
        result["news"] = {"error": str(e)}

    try:
        from kill_switch import get_status
        result["kill_switch"] = get_status()
    except Exception as e:
        result["kill_switch"] = {"error": str(e)}

    try:
        from circuit_breaker import drawdown_circuit_breaker
        result["circuit_breaker"] = drawdown_circuit_breaker.get_status()
    except Exception as e:
        result["circuit_breaker"] = {"error": str(e)}

    return result
