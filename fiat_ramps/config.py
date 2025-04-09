# fiat_ramps/config.py

import os

# Transak API Configuration
TRANSAK_API_KEY = os.getenv("TRANSAK_API_KEY", "")
REDIRECT_URL = os.getenv("TRANSAK_REDIRECT_URL", "https://ccip.chain.link/")
WEBHOOK_PORT = int(os.getenv("FIAT_WEBHOOK_PORT", 5000))
