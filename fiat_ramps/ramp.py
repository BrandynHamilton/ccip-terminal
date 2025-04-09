from urllib.parse import urlencode

def create_ramp_url(wallet_address, amount=100, network="ARBITRUM", crypto="ETH", fiat="USD", app_name="CCIP-Terminal"):
    """
    Create a Ramp Network fiat-onramp URL.

    Args:
        wallet_address (str): Wallet address to receive funds.
        amount (float): Amount in fiat currency.
        network (str): Blockchain network (e.g., 'ARBITRUM', 'ETHEREUM').
        crypto (str): Token to purchase (e.g., 'ETH', 'USDC').
        fiat (str): Fiat currency (e.g., 'USD', 'EUR').
        app_name (str): Your dApp or CLI name (used in widget header).

    Returns:
        str: Ramp Network onramp URL
    """
    query = {
        "userAddress": wallet_address,
        "defaultAsset": f"{crypto.upper()}_{network.upper()}",
        "fiatCurrency": fiat.upper(),
        "fiatValue": int(amount),
        "hostAppName": app_name,
    }

    url = f"https://buy.ramp.network/?{urlencode(query)}"
    print(f"🔗 Ramp On-Ramp URL:\n{url}")
    return url
