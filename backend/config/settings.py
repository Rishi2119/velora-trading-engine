"""
Velora Backend — Configuration
All settings loaded from environment variables with sensible defaults.
"""
import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
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
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"
    
    # ── Google / Firebase ────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    FIREBASE_PROJECT_ID: str = "velora-trading"
    ENABLE_FIREBASE: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    # ── Database ──────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./velora.db"

    # ── MT5 Credentials ───────────────────────────────────────────
    MT5_ACCOUNT: int = 0
    MT5_PASSWORD: str = ""
    MT5_SERVER: str = ""
    MT5_PATH: str = ""

    # ── Existing Flask Mobile API ─────────────────────────────────
    MOBILE_API_URL: str = "http://127.0.0.1:5050"
    MOBILE_API_TOKEN: str = ""

    # ── AI / Neural Engine ───────────────────────────────────────
    VELORA_API_KEY: str = ""
    AI_ENGINE_TYPE: str = "openrouter" # "local" or "openrouter"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "deepseek/deepseek-chat"


    # ── Supabase (optional SaaS layer) ────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ── Stripe (optional billing) ─────────────────────────────────
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""


    # ── Trading defaults ──────────────────────────────────────────
    ACCOUNT_BALANCE: float = 500.0
    RISK_PER_TRADE: float = 0.01
    MIN_RISK_REWARD: float = 3.0
    MAX_DAILY_LOSS: float = 20.0
    MAX_DAILY_TRADES: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
