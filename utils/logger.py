import logging
import functools
import time
from typing import Any, Callable, Optional


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given module name."""
    return logging.getLogger(name)


class Logger:
    """Wrapper around Python's logging module with convenience methods."""

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    def info(self, message: str, **kwargs: Any) -> None:
        extra = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self._logger.info(f"{message} {extra}".strip())

    def warning(self, message: str, **kwargs: Any) -> None:
        extra = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self._logger.warning(f"{message} {extra}".strip())

    def error(self, message: str, **kwargs: Any) -> None:
        extra = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self._logger.error(f"{message} {extra}".strip())

    def debug(self, message: str, **kwargs: Any) -> None:
        extra = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self._logger.debug(f"{message} {extra}".strip())

    def exception(self, message: str, exc: Optional[Exception] = None) -> None:
        if exc:
            self._logger.exception(f"{message}: {exc}")
        else:
            self._logger.exception(message)


def log_function_call(func: Callable) -> Callable:
    """Decorator that logs function entry, exit, and duration."""
    logger = get_logger(func.__module__)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} args={args[:2]} kwargs={list(kwargs.keys())}")
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug(f"{func.__name__} completed in {elapsed:.1f}ms")
            return result
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(f"{func.__name__} failed after {elapsed:.1f}ms: {exc}")
            raise

    return wrapper


def structured_log(logger: logging.Logger, level: str, event: str, **fields: Any) -> None:
    """Log a structured event with key-value pairs."""
    parts = [f"event={event}"]
    parts.extend(f"{k}={v}" for k, v in fields.items())
    message = " | ".join(parts)
    getattr(logger, level.lower(), logger.info)(message)
