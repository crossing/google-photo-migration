import logging
import random
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def rate_limit_retry(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()
                    # Check for rate limit indicators in error message
                    indicators = ["429", "rate_limit", "too many requests", "quota"]
                    if any(indicator in error_str for indicator in indicators):
                        retries += 1
                        if retries >= max_retries:
                            logger.error(
                                f"Max retries reached for {func.__name__} after {retries} attempts."
                            )
                            raise

                        delay = min(base_delay * (2**retries) + random.uniform(0, 1), max_delay)
                        logger.warning(
                            f"Rate limit hit in {func.__name__}. "
                            f"Retrying in {delay:.2f}s (Attempt {retries}/{max_retries})..."
                        )
                        time.sleep(delay)
                    else:
                        raise

        return wrapper  # type: ignore

    return decorator
