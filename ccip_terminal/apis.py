from ccip_terminal.env import (COINGECKO_API_KEY)
from ccip_terminal.decorators import api_cache

import requests
import pandas as pd
import time

@api_cache
def token_data(id='usd-coin', network=None, contract_address=None, timeout=10):
    """
    Fetch token data from CoinGecko API.

    Args:
        id (str): CoinGecko token ID. If None, both `network` and `contract_address` must be provided.
        network (str): Blockchain network (e.g., 'ethereum').
        contract_address (str): Token contract address.
        timeout (int): Timeout for the API request in seconds.

    Returns:
        dict: Token data from CoinGecko.

    Raises:
        ValueError: If required parameters are missing or invalid.
        RuntimeError: For HTTP/network errors or invalid API responses.
    """
    if id:
        url = f"https://api.coingecko.com/api/v3/coins/{id}"
    elif network and contract_address:
        url = f"https://api.coingecko.com/api/v3/coins/{network}/contract/{contract_address}"
    else:
        raise ValueError("Either `id` OR both `network` and `contract_address` must be provided.")

    headers = {
        "accept": "application/json"
    }

    # Include API key in headers if available
    if COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # Raises HTTPError for bad status codes
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Invalid response format.")
        return data
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch token data: {e}")
    except ValueError as e:
        raise RuntimeError(f"Invalid API response: {e}")
