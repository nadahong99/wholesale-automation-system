# utils/decorators.py
import time
import functools
from typing import Callable, Tuple, Type
from utils.logger import get_logger

logger = get_logger("decorators")


def retry_on_exception(
    retries: int = 3,
    delay: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger_name: str = "retry",
):
    """Decorator that retries the wrapped function on specified exceptions."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = get_logger(logger_name)
            last_exc = None
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    _logger.warning(
                        f"[{func.__name__}] Attempt {attempt}/{retries} failed: {exc}"
                    )
                    if attempt < retries:
                        time.sleep(delay)
            _logger.error(f"[{func.__name__}] All {retries} attempts failed.")
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


def log_execution_time(func: Callable) -> Callable:
    """Decorator that logs the execution time of the wrapped function."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"[{func.__name__}] completed in {elapsed:.3f}s")
        return result

    return wrapper


def handle_errors(default=None, log_level: str = "error"):
    """Decorator that catches all exceptions and returns *default* value."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                log_fn = getattr(logger, log_level, logger.error)
                log_fn(f"[{func.__name__}] Unhandled exception: {exc}", exc_info=True)
                return default

        return wrapper

    return decorator
