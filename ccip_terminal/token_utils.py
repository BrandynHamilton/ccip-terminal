from web3 import Web3

def get_balance(TOKEN_CONTRACTS, TOKEN_DECIMALS, ACCOUNT_ADDRESS,w3):
    """Fetch token balances using Web3 with provided decimal adjustments."""
    try:
        # ERC20 ABI for balanceOf function
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]

        # Fetch balances using the provided decimals
        balances = {}
        for token, address in TOKEN_CONTRACTS.items():
            decimals = TOKEN_DECIMALS.get(token)

            if address and decimals is not None:
                try:
                    contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=erc20_abi)
                    balance_wei = contract.functions.balanceOf(ACCOUNT_ADDRESS).call()
                    balances[token] = balance_wei / 10**decimals
                except Exception as e:
                    print(f"Error fetching balance for {token}: {e}")
                    balances[token] = None
            else:
                print(f"Skipping {token} due to missing address or decimals.")
                balances[token] = None
        return balances

    except Exception as e:
        print(f"Error fetching balances: {e}")
        return None