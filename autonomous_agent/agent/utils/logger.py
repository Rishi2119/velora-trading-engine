import logging
import os
import sys
from datetime import datetime


def setup_logger(name="autonomous_agent"):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File handler — always UTF-8 so emojis go to the log file fine
    log_file = os.path.join(log_dir, f"agent_{datetime.now().strftime('%Y%m%d')}.log")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    # Console handler — force UTF-8 on Windows (cp1252 can't render box-drawing / emoji)
    if sys.platform == "win32":
        # Wrap stdout in a UTF-8 writer so emoji / box-drawing chars don't crash
        try:
            import io
            utf8_stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
            )
        except AttributeError:
            # sys.stdout.buffer unavailable (e.g. IDLE / some IDEs) — fall back gracefully
            utf8_stdout = sys.stdout
        ch = logging.StreamHandler(utf8_stdout)
    else:
        ch = logging.StreamHandler(sys.stdout)

    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


logger = setup_logger()
