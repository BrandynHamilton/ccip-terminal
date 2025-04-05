# usdc_transfer/decorators.py
from cachetools import TTLCache, cached
from usdc_transfer.config import config
from functools import wraps

def get_cache():
    if config.CACHE_ENABLED:
        return TTLCache(maxsize=config.CACHE_MAXSIZE, ttl=config.CACHE_TTL)
    return None

def api_cache(func):
    def wrapper(*args, use_cache=True, **kwargs):
        cache = get_cache()
        if use_cache and cache:
            return cached(cache)(func)(*args, **kwargs)
        return func(*args, **kwargs)
    return wrapper

def ttl_cache(ttl=None, maxsize=None):
    """
    Decorator factory that allows setting custom TTL per function.
    Falls back to config defaults if not provided.
    """
    def decorator(func):
        cache = TTLCache(
            maxsize=maxsize or config.CACHE_MAXSIZE,
            ttl=ttl or config.CACHE_TTL
        )
        @cached(cache)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
