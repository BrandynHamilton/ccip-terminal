import os
from web3 import Web3
from ccip_terminal.network import network_func

def load_accounts(network='ethereum', account_index=None, password=None):
    private_keys = os.getenv("PRIVATE_KEYS", "").split(",")
    accounts = []

    # Load from .env if present
    env_keys = [key.strip() for key in private_keys if key.strip()]
    if env_keys:
        for key in env_keys:
            w3 = network_func(network)
            account = w3.eth.account.from_key(key)
            accounts.append({"w3": w3, "account": account})

    # If no .env keys or fallback needed
    if not accounts and os.path.exists("wallet_keystore.json"):
        from ccip_terminal.wallet import decrypt_keystore
        try:
            if password is None:
                from getpass import getpass
                password = getpass("Enter password for encrypted wallet: ")

            key = decrypt_keystore(password)
            w3 = network_func(network)
            account = w3.eth.account.from_key(key)
            accounts.append({"w3": w3, "account": account})
        except Exception as e:
            raise Exception(f"Failed to decrypt keystore: {e}")

    if not accounts:
        raise ValueError("No private keys found in .env or encrypted wallet.")

    # Handle specific index
    if account_index is not None:
        try:
            return [accounts[account_index]]
        except IndexError:
            raise IndexError(f"No private key found at index {account_index}")

    return accounts





