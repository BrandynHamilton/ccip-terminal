# usdctransfer/config.py

class APIConfig:
    CACHE_ENABLED = True
    CACHE_TTL = 900  # default 15 minutes
    CACHE_MAXSIZE = 100

config = APIConfig()
