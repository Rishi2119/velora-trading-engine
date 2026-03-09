import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "http://localhost:54321")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "dummy_service_role_key")
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "sk_test_123")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_123")
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
