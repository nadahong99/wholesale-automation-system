# utils/logger.py
from config.logging import get_logger as _get_logger
import logging


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    return _get_logger(name, level)
