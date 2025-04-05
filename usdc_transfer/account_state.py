from usdc_transfer.utils import (extract_token_decimals,extract_token_contracts,
                                to_checksum_dict)
from usdc_transfer.apis import token_data
from usdc_transfer.accounts import load_accounts, network_func
from usdc_transfer.token_utils import get_balance
import json

def get_all_balances(TOKEN_CONTRACTS, TOKEN_DECIMALS):
    BALANCE_DICT = {}

    for account_obj in load_accounts():
        account = account_obj["account"]
        address = account.address

        BALANCE_DICT[address] = {}

        for chain_name, token_address in TOKEN_CONTRACTS.items():
            try:
                # Create chain-specific Web3 connection
                w3_chain = network_func(chain_name)

                # ERC20 balance
                single_token_dict = get_balance(
                    {chain_name: token_address}, 
                    TOKEN_DECIMALS, 
                    address, 
                    w3_chain
                )

                # Native gas token balance
                native_balance_wei = w3_chain.eth.get_balance(address)
                native_balance_eth = w3_chain.from_wei(native_balance_wei, "ether")

                # Combine
                BALANCE_DICT[address][chain_name] = {
                    "usdc": single_token_dict[chain_name],
                    "native_token": float(native_balance_eth)
                }

            except Exception as e:
                print(f"❌ Failed to fetch balances for {chain_name} / {address}: {e}")
                BALANCE_DICT[address][chain_name] = {
                    "usdc": None,
                    "native_token": None
                }

    print(json.dumps(BALANCE_DICT, indent=2))
    return BALANCE_DICT

def get_usdc_data():

    usdc_data = token_data()
    TOKEN_DECIMALS = extract_token_decimals(usdc_data)
    TOKEN_CONTRACTS = extract_token_contracts(usdc_data)
    BALANCES_DICT = get_all_balances(TOKEN_CONTRACTS,TOKEN_DECIMALS)
    TOKEN_CONTRACTS = to_checksum_dict(TOKEN_CONTRACTS)

    return BALANCES_DICT, TOKEN_CONTRACTS, TOKEN_DECIMALS
