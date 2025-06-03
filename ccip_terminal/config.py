# usdctransfer/config.py

import os
from dotenv import load_dotenv
load_dotenv()

class APIConfig:
    CACHE_ENABLED = True
    CACHE_TTL = 900  # default 15 minutes
    CACHE_MAXSIZE = 100

config = APIConfig()

class Settings:
    NETWORK_TYPE = os.getenv('NETWORK_TYPE', 'mainnet')

settings = Settings()
