"""
Exponential backoff retry decorator for unreliable external API calls.
"""

import asyncio
import functools
import logging
from typing import Tuple, Type

logger = logging.getLogger(__name__)

DEFAULT_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 30.0


def retry(
    retries: int = DEFAULT_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Async retry decorator with exponential backoff.

    Args:
        retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Cap on the delay between retries
        exceptions: Tuple of exception types to catch and retry
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"Retry {attempt + 1}/{retries} for {func.__name__}: {e}. "
                            f"Waiting {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {retries} retries exhausted for {func.__name__}: {e}"
                        )
            raise last_exception

        return wrapper

    return decorator
