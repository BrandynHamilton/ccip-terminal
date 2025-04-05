# fiat_ramps/transak.py

import requests
from .config import TRANSAK_API_KEY, REDIRECT_URL
from usdc_transfer.metadata import FALLBACK_GAS_TOKENS
from usdc_transfer.decorators import ttl_cache

@ttl_cache(ttl=86400)  # Cache per wallet validation for 24 hours
def verify_address(wallet_address,crypto_currency_code='USDC',network="ethereum"):

    url = f"https://api-stg.transak.com/api/v2/currencies/verify-wallet-address?cryptoCurrency={crypto_currency_code}&network={network}&walletAddress={wallet_address}"

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)

    print(response.text)

@ttl_cache(ttl=3600)  # 1 hour
def get_supported_cryptocurrencies():
    """
    Fetch the list of supported cryptocurrencies from Transak.

    Returns:
        list: A list of supported cryptocurrency codes.
    """
    url = "https://api.transak.com/api/v2/currencies/crypto-currencies"
    response = requests.get(url)
    data = response.json()
    return [crypto['code'] for crypto in data]

@ttl_cache(ttl=86400)  # 24 hours
def get_transak_token_metadata():
    """Fetch supported cryptocurrencies from Transak and map gas tokens per network."""
    TRANSAK_CURRENCIES_URL = "https://api.transak.com/api/v2/currencies/crypto-currencies"
    try:
        response = requests.get(TRANSAK_CURRENCIES_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        token_map = {}

        for token in data.get("response", []):
            network = token["network"]["name"].lower()
            if token["symbol"] in ["ETH", "AVAX", "MATIC"] and token["isAllowed"]:
                token_map[network] = token["symbol"]

        return token_map
    except Exception as e:
        print(f"⚠️ Failed to fetch Transak metadata, falling back: {e}")
        return FALLBACK_GAS_TOKENS

def create_transak_session(wallet_address, amount, network="ethereum",purchase_type='usdc'):
    """
    Create a Transak payment session.

    Args:
        wallet_address (str): Destination wallet.
        amount (float): Fiat amount in USD.
        crypto_currency_code (str): Cryptocurrency code to purchase (e.g., 'ETH' for gas, 'USDC' for stablecoin).
        network (str): Blockchain network.

    Returns:
        dict: Transak session data.
    """
    token_map = get_transak_token_metadata()

    crypto_currency_code = "USDC" if purchase_type == "usdc" else token_map.get(network, FALLBACK_GAS_TOKENS[network])

    url = "https://api.transak.com/api/v2/transactions"
    payload = {
        "apiKey": TRANSAK_API_KEY,
        "walletAddress": wallet_address,
        "fiatAmount": amount,
        "cryptoCurrencyCode": crypto_currency_code,
        "fiatCurrency": "USD",
        "network": network,
        "redirectURL": REDIRECT_URL,
    }

    response = requests.post(url, json=payload)
    data = response.json()

    if data.get("status") != "SUCCESS":
        raise Exception(f"Failed to create Transak session: {data.get('message')}")

    print(f"🔗 Payment link: {data['data']['url']}")
    return data
