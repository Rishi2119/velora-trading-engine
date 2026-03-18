import logging
import os
import sys
from datetime import datetime

def get_logger(name="VeloraAI"):
    """
    Returns a structured logger with both console and file handlers.
    Ensures safe UTF-8 output on Windows for emojis and special characters.
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if logger is already initialized
    if logger.hasHandlers():
        logger.handlers.clear()

    # Standard format for logs
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. File Handler (Rotating logs would be better, but keeping it simple for now)
    log_file = os.path.join(log_dir, "velora_engine.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 2. Console Handler
    # On Windows, we need to handle potential encoding issues with emojis/box-drawing chars
    if sys.platform == "win32":
        try:
            import io
            # Wrap stdout to ensure it supports UTF-8
            stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
            console_handler = logging.StreamHandler(stream)
        except (AttributeError, io.UnsupportedOperation):
            console_handler = logging.StreamHandler(sys.stdout)
    else:
        console_handler = logging.StreamHandler(sys.stdout)

    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
