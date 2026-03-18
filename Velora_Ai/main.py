# // turbo
"""
Velora AI Engine V2.0 — One-Click Entry Point
Run: python main.py
"""
import asyncio
import uvicorn
import threading
from loguru import logger
from pathlib import Path

LOG_DIR = Path("D:/trading_engins/Velora_Ai/logs")
LOG_DIR.mkdir(exist_ok=True)
logger.add(LOG_DIR / "velora_{time:YYYY-MM-DD}.log", rotation="1 day", retention="30 days", level="INFO")

def run_api():
    import sys
    import os
    sys.path.insert(0, os.getcwd())
    import api.main_api as api_module
    uvicorn.run("api.main_api:app", host="0.0.0.0", port=8000, log_level="warning")

async def run_trading_engine():
    from core.trading_engine import engine
    await engine.run(interval_seconds=300)

async def main():
    logger.info("="*60)
    logger.info("  VELORA AI ENGINE V2.0 — Starting...")
    logger.info("  Powered by: DeepSeek AI + MetaTrader 5 + FastAPI")
    logger.info("="*60)

    # Start FastAPI in background thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    logger.success("[API] FastAPI running on http://localhost:8000")

    # Run trading engine on main async loop
    await run_trading_engine()

if __name__ == "__main__":
    asyncio.run(main())
