import os
from web3 import Web3
from usdc_terminal.network import network_func

def load_accounts(network='ethereum'):
    private_keys = os.getenv("PRIVATE_KEYS", "").split(",")
    accounts = []

    for i, key in enumerate(private_keys, start=1):
        if key.strip():
            w3 = network_func(network)
            account = w3.eth.account.from_key(key.strip())
            print(f'account {i}: {account.address}')
            accounts.append({"w3": w3, "account": account})
    return accounts

