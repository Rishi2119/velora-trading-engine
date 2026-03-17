"""
Velora Backend — Configuration
All settings loaded from environment variables with sensible defaults.
"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "Velora Trading API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Security ─────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "velora-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24
    # Comma-separated allowed CORS origins
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ── Database ──────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./velora.db"

    # ── MT5 Credentials ───────────────────────────────────────────
    MT5_ACCOUNT: int = 0
    MT5_PASSWORD: str = ""
    MT5_SERVER: str = ""

    # ── Existing Flask Mobile API ─────────────────────────────────
    MOBILE_API_URL: str = "http://127.0.0.1:5050"
    MOBILE_API_TOKEN: str = ""

    # ── AI / NVIDIA ───────────────────────────────────────────────
    KIMI_API_KEY: str = ""
    NVIDIA_API_KEY: str = ""

    # ── Supabase (optional SaaS layer) ────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # ── Stripe (optional billing) ─────────────────────────────────
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ── Trading defaults ──────────────────────────────────────────
    ACCOUNT_BALANCE: float = 500.0
    RISK_PER_TRADE: float = 0.01
    MIN_RISK_REWARD: float = 3.0
    MAX_DAILY_LOSS: float = 20.0
    MAX_DAILY_TRADES: int = 5


settings = Settings()
