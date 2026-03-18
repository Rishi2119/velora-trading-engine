# // turbo
"""
Velora AI Engine V2.0 — Environment Bootstrap
Run this FIRST before anything else.
"""
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path("D:/trading_engins/Velora_Ai")

DIRS = [
    "ai", "api", "core", "data", "models", "logs",
    "tests", "config", "utils", "frontend"
]

PACKAGES = [
    "MetaTrader5", "fastapi", "uvicorn[standard]", "supabase",
    "pandas", "numpy", "scikit-learn", "joblib", "httpx",
    "python-dotenv", "aiohttp", "websockets", "ta", "pytz",
    "pydantic>=2.0", "apscheduler", "loguru", "pytest",
    "pytest-asyncio", "requests"
]

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[WARN] {cmd}: {result.stderr.strip()}")
    return result.returncode == 0

def main():
    print("[Velora] Creating directory structure...")
    for d in DIRS:
        (ROOT / d).mkdir(parents=True, exist_ok=True)
        init = ROOT / d / "__init__.py"
        if not init.exists():
            init.write_text("")

    print("[Velora] Installing packages...")
    for pkg in PACKAGES:
        success = run(f"{sys.executable} -m pip install {pkg} -q")
        status = "OK" if success else "WARN"
        print(f"  [{status}] {pkg}")

    env_file = ROOT / ".env"
    if not env_file.exists():
        env_file.write_text("""# Velora AI Engine V2.0 — Environment Variables
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_mt5_server
MT5_PATH=C:/Program Files/MetaTrader 5/terminal64.exe
VELORA_ENV=development
MAX_RISK_PER_TRADE=0.01
MAX_DAILY_LOSS=0.03
MAX_DRAWDOWN=0.10
MAX_CONCURRENT_TRADES=3
NEWS_BLACKOUT_MINUTES=30
DEFAULT_PAIRS=EURUSD,GBPUSD,USDJPY,AUDUSD,GBPJPY
""")
        print("[Velora] .env file created — fill in your credentials")

    print("\n[Velora] Setup complete. Fill .env then run: python main.py")

if __name__ == "__main__":
    main()
