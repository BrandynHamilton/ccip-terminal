from usdc_transfer.env import (COINGECKO_API_KEY)
from usdc_transfer.decorators import api_cache

import requests
import pandas as pd
import time

@api_cache
def token_data(id='usd-coin', network=None, contract_address=None, timeout=10):
    """
    Fetch token data from Coingecko API.
    
    Args:
        id (str): Coingecko token ID. If None, both `network` and `contract_address` must be provided.
        network (str): Blockchain network (e.g., 'ethereum').
        contract_address (str): Token contract address.
    
    Returns:
        dict: Token data from Coingecko.
    
    Raises:
        ValueError: If required parameters are missing or invalid.
        requests.exceptions.RequestException: For HTTP/network errors.
    """
    if not COINGECKO_API_KEY:
        raise ValueError("COINGECKO_API_KEY is missing or empty.")

    if id:
        url = f"https://api.coingecko.com/api/v3/coins/{id}"
    elif network and contract_address:
        url = f"https://api.coingecko.com/api/v3/coins/{network}/contract/{contract_address}"
    else:
        raise ValueError("Either `id` OR both `network` and `contract_address` must be provided.")

    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": COINGECKO_API_KEY
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # raises HTTPError for bad status codes
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Invalid response format.")
        return data
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch token data: {e}")
    except ValueError as e:
        raise RuntimeError(f"Invalid API response: {e}")
