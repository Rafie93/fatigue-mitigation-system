"""Application logging. All logs go to storage/logs (PRD §17).

Sensitive values (desktop password, device tokens) are never logged."""
import logging
import os
from logging.handlers import RotatingFileHandler

from services.paths import LOGS_DIR


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    log_path = os.path.join(LOGS_DIR, "app.log")
    logger = logging.getLogger("fatigue")
    if logger.handlers:  # already configured
        return logger
    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    logger.addHandler(stream)

    logger.info("Logging initialised at %s", log_path)
    return logger
