import functools
import logging
import time
import threading
from typing import Any, Callable, Optional, Tuple, Type

_rate_limit_lock = threading.Lock()
_rate_limit_calls: dict = {}


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """Retry a function up to max_retries times on specified exceptions."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: Exception = RuntimeError("No attempts")
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))
            raise last_exc
        return wrapper
    return decorator


def timer(func: Callable) -> Callable:
    """Log the execution time of a function."""
    logger = logging.getLogger(func.__module__)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(f"{func.__name__} took {elapsed:.2f}ms")
        return result

    return wrapper


def cache_result(ttl_seconds: int = 300) -> Callable:
    """Cache function result for ttl_seconds. Cache is per unique args."""
    def decorator(func: Callable) -> Callable:
        cache: dict = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            if key in cache:
                result, ts = cache[key]
                if now - ts < ttl_seconds:
                    return result
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result

        wrapper.cache_clear = lambda: cache.clear()  # type: ignore[attr-defined]
        return wrapper
    return decorator


def validate_input(**validators: Callable) -> Callable:
    """Validate keyword arguments using provided validator callables."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    if not validator(kwargs[param_name]):
                        raise ValueError(
                            f"Validation failed for parameter '{param_name}': "
                            f"value={kwargs[param_name]!r}"
                        )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_errors(logger: Optional[logging.Logger] = None) -> Callable:
    """Log any exceptions raised by the decorated function."""
    def decorator(func: Callable) -> Callable:
        _logger = logger or logging.getLogger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                _logger.error(f"{func.__name__} raised {type(exc).__name__}: {exc}")
                raise

        return wrapper
    return decorator


def rate_limit(calls_per_second: float = 1.0) -> Callable:
    """Limit how often a function can be called per second."""
    min_interval = 1.0 / calls_per_second
    last_called: dict = {"ts": 0.0}
    lock = threading.Lock()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                now = time.monotonic()
                elapsed = now - last_called["ts"]
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)
                last_called["ts"] = time.monotonic()
            return func(*args, **kwargs)
        return wrapper
    return decorator
