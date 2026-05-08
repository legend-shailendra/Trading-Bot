"""
logging_config.py
-----------------
Configures the application-wide logger to write to both the console
and a rotating log file (trading_bot.log).
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trading_bot.log")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.DEBUG) -> logging.Logger:
    """
    Set up and return the root logger for the trading bot.

    Creates a rotating file handler (max 5 MB, 3 backups) and a
    stream handler so messages appear in the console as well.

    Args:
        level: Logging level (default: DEBUG).

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger("trading_bot")

    # Prevent duplicate handlers when called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # --- Rotating File Handler ---
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # --- Stream (Console) Handler ---
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    logger.info("Logging initialised. Log file: %s", LOG_FILE)
    return logger


# Module-level logger obtained once at import time so other modules can do:
#   from bot.logging_config import logger
logger = setup_logging()
