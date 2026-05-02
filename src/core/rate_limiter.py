import time
import logging
import random
from functools import wraps

logger = logging.getLogger(__name__)

def rate_limit_retry(max_retries=5, base_delay=1.0, max_delay=60.0):
    """
    Decorator for retrying API calls with exponential backoff on rate limits.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()
                    # Check for rate limit indicators in error message
                    if any(indicator in error_str for indicator in ["429", "rate_limit", "too many requests", "quota"]):
                        retries += 1
                        if retries >= max_retries:
                            logger.error(f"Max retries reached for {func.__name__} after {retries} attempts.")
                            raise
                        
                        delay = min(base_delay * (2 ** retries) + random.uniform(0, 1), max_delay)
                        logger.warning(f"Rate limit hit in {func.__name__}. Retrying in {delay:.2f}s (Attempt {retries}/{max_retries})...")
                        time.sleep(delay)
                    else:
                        # For other exceptions, just raise them
                        raise
            return func(*args, **kwargs)
        return wrapper
    return decorator
