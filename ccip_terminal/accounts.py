import os
from web3 import Web3
from ccip_terminal.network import network_func

def load_accounts(network='ethereum', account_index=None):
    private_keys = os.getenv("PRIVATE_KEYS", "").split(",")

    # If a specific index is provided, extract that one key only
    if account_index is not None:
        try:
            key = private_keys[account_index].strip()
            if not key:
                raise ValueError(f"Empty private key at index {account_index}")
            w3 = network_func(network)
            account = w3.eth.account.from_key(key)
            return [{"w3": w3, "account": account}]
        except IndexError:
            raise IndexError(f"No private key found at index {account_index}")
    else:
        # Otherwise, load all accounts
        accounts = []
        for i, key in enumerate(private_keys):
            if key.strip():
                w3 = network_func(network)
                account = w3.eth.account.from_key(key.strip())
                accounts.append({"w3": w3, "account": account})
        return accounts




