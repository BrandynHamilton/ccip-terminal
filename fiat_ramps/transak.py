# fiat_ramps/transak.py

import requests
from urllib.parse import urlencode
from .config import TRANSAK_API_KEY, REDIRECT_URL
from ccip_terminal.metadata import FALLBACK_GAS_TOKENS
from ccip_terminal.decorators import ttl_cache

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

def create_transak_session(wallet_address, amount, network="ethereum", purchase_type='usdc'):
    """
    Create a Transak session URL to redirect the user.

    Args:
        wallet_address (str): Destination wallet.
        amount (float): Fiat amount in USD.
        network (str): Blockchain network.
        purchase_type (str): 'usdc' or 'gas' (to determine which token to use)

    Returns:
        str: Transak URL for initiating payment
    """
    token_map = get_transak_token_metadata()
    crypto_currency_code = "USDC" if purchase_type == "usdc" else token_map.get(network, FALLBACK_GAS_TOKENS[network])

    base_url = "https://global.transak.com/"
    query_params = {
        "apiKey": TRANSAK_API_KEY,
        "walletAddress": wallet_address,
        "cryptoCurrencyCode": crypto_currency_code,
        "network": network,
        "fiatCurrency": "USD",
        "fiatAmount": int(amount),
        "redirectURL": REDIRECT_URL,
        "disableWalletAddressForm": "true",
        "productsAvailed": "BUY",
        "themeColor": "000000",
        "colorMode": "DARK"
    }

    full_url = f"{base_url}?{urlencode(query_params)}"
    print(f"🔗 Transak On-Ramp URL: {full_url}")
    return full_url
