# // turbo
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path("D:/trading_engins/Velora_Ai/.env"))

class VeloraConfig:
    # DeepSeek AI
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # MetaTrader 5
    try:
        MT5_LOGIN: int = int(os.getenv("MT5_LOGIN", "0"))
    except ValueError:
        MT5_LOGIN: int = 0
    MT5_PASSWORD: str = os.getenv("MT5_PASSWORD", "")
    MT5_SERVER: str = os.getenv("MT5_SERVER", "")
    MT5_PATH: str = os.getenv("MT5_PATH", "")

    # Risk Rules — HARDCODED GUARDRAILS (cannot be overridden by AI)
    MAX_RISK_PER_TRADE: float = float(os.getenv("MAX_RISK_PER_TRADE", "0.01"))
    MAX_DAILY_LOSS: float = float(os.getenv("MAX_DAILY_LOSS", "0.03"))
    MAX_DRAWDOWN: float = float(os.getenv("MAX_DRAWDOWN", "0.10"))
    MAX_CONCURRENT_TRADES: int = int(os.getenv("MAX_CONCURRENT_TRADES", "3"))
    NEWS_BLACKOUT_MINUTES: int = int(os.getenv("NEWS_BLACKOUT_MINUTES", "30"))

    # Trading Universe
    DEFAULT_PAIRS: list = os.getenv(
        "DEFAULT_PAIRS", "EURUSD,GBPUSD,USDJPY,AUDUSD,GBPJPY"
    ).split(",")

    TIMEFRAMES = {
        "M15": 15, "M30": 30, "H1": 60,
        "H4": 240, "D1": 1440, "W1": 10080
    }

    # Paths
    ROOT: Path = Path("D:/trading_engins/Velora_Ai")
    DATA_PATH: Path = ROOT / "data" / "strategies.json"
    MODELS_PATH: Path = ROOT / "models"
    LOGS_PATH: Path = ROOT / "logs"

config = VeloraConfig()
