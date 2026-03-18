"""
Velora — Structured Logger
JSON-formatted rotating file logger + colored console output.
"""
import logging
import logging.handlers
import os
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "source": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logging(log_dir: str = "logs") -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # ── Console handler (plain text) ──────────────────────────────
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(
        logging.Formatter(
            "%(asctime)s  [%(levelname)-8s]  %(name)s — %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root.addHandler(console)

    # ── Rotating JSON file handler ────────────────────────────────
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "velora_backend.log"),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    root.addHandler(file_handler)

    # ── Error-only file handler ───────────────────────────────────
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "velora_errors.log"),
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root.addHandler(error_handler)

    # Silence noisy third-party loggers
    for noisy in ("sqlalchemy.engine", "httpx", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    return root


logger = setup_logging()
