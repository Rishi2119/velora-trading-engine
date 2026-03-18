"""
Velora — Structured JSON logger for production.
"""
import logging
import os
import sys
from backend.app.core.config import config

LOG_LEVEL = getattr(logging, config.log_level.upper(), logging.INFO)

os.makedirs("logs", exist_ok=True)

# JSON-format handler for production; human-readable for dev
_fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

logging.basicConfig(
    level=LOG_LEVEL,
    format=_fmt,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/engine.log", encoding="utf-8"),
    ],
)

# Suppress noisy third-party loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Factory — every module calls get_logger(__name__)."""
    return logging.getLogger(name)
