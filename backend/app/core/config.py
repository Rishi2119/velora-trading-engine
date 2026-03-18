"""
Velora Engine — Centralized Configuration
All settings from environment variables, typed with pydantic-settings.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, AliasChoices
import os


class VeloraConfig(BaseSettings):
    # ── MT5 ──────────────────────────────────────────────────────────────────
    mt5_account: int = Field(0, validation_alias=AliasChoices("MT5_ACCOUNT", "MT5_LOGIN"))
    mt5_password: str = Field("", validation_alias=AliasChoices("MT5_PASSWORD", "MT5_PASS"))
    mt5_server: str = Field("", validation_alias=AliasChoices("MT5_SERVER", "MT5_SRV"))
    mt5_magic_number: int = 234000

    # ── Strategy ─────────────────────────────────────────────────────────────
    risk_per_trade_pct: float = 0.01
    max_daily_loss_pct: float = 0.05
    circuit_breaker_pct: float = 0.05
    max_spread_pips: float = 3.0
    max_positions: int = 3
    max_trades_per_day: int = 10
    max_symbol_exposure_pct: float = 0.05
    slippage_tolerance_pips: float = 2.0
    adx_trend_threshold: int = 25
    ema_fast: int = 50
    ema_slow: int = 200
    rsi_period: int = 14
    rsi_pullback_max: int = 52
    min_risk_reward: float = 3.0
    timeframe: str = "M15"
    pairs: str = "EURUSD,GBPUSD"
    symbol: str = "EURUSD"

    # ── Infrastructure ────────────────────────────────────────────────────────
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    api_secret_key: str = "velora-super-secret-key-change-in-production"
    allowed_origins: str = "http://localhost:3000"
    engine_mode: str = "paper"
    log_level: str = "INFO"
    port: int = 8000

    # ── Encryption ────────────────────────────────────────────────────────────
    # Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    encryption_key: str = ""

    # ── Copy trading ──────────────────────────────────────────────────────────
    copy_trading_enabled: bool = False
    master_account_id: str = ""

    # ── Derived ───────────────────────────────────────────────────────────────
    @property
    def pairs_list(self) -> List[str]:
        return [p.strip() for p in self.pairs.split(",") if p.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_live(self) -> bool:
        return self.engine_mode.lower() == "live"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "case_sensitive": False,
    }


# Singleton — import this everywhere
config = VeloraConfig()
