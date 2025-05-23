from ccip_terminal.utils import (extract_token_decimals,extract_token_contracts,
                                to_checksum_dict, get_largest_balance)
from ccip_terminal.apis import token_data
from ccip_terminal.accounts import load_accounts, network_func
from ccip_terminal.token_utils import get_balance
import json

def get_all_balances(TOKEN_CONTRACTS, TOKEN_DECIMALS, account_index=None, account_obj=None, only_chain=None):
    if isinstance(account_obj, dict):
        account_obj = [account_obj]

    BALANCE_DICT = {}

    if account_obj is None:
        account_obj = load_accounts(account_index=account_index)

    for obj in account_obj:
        account = obj["account"]
        address = account.address
        BALANCE_DICT[address] = {}

        for chain_name, token_address in TOKEN_CONTRACTS.items():
            if only_chain and chain_name != only_chain:
                continue

            try:
                w3_chain = (
                    obj["w3"]
                    if obj.get("w3") and obj["w3"].eth.chain_id == network_func(chain_name).eth.chain_id
                    else network_func(chain_name)
                )

                single_token_dict = get_balance(
                    {chain_name: token_address},
                    TOKEN_DECIMALS,
                    address,
                    w3_chain
                )

                native_balance_wei = w3_chain.eth.get_balance(address)
                native_balance_eth = w3_chain.from_wei(native_balance_wei, "ether")

                BALANCE_DICT[address][chain_name] = {
                    "usdc": single_token_dict[chain_name],
                    "native_token": float(native_balance_eth)
                }

            except Exception as e:
                print(f"Failed to fetch balances for {chain_name} / {address}: {e}")
                BALANCE_DICT[address][chain_name] = {
                    "usdc": None,
                    "native_token": None
                }

    return BALANCE_DICT, account_obj

def prepare_transfer_data(dest_chain, source_chain=None, account_index=None, account_obj=None, min_gas_threshold=0.001):
    """
    Prepares all required data for a CCIP transfer in one call.
    Dynamically selects account_index and source_chain if not provided.
    Always returns a single account object (with .w3) for the selected source_chain.
    """
    print(f'min_gas_threshold at prepare transfer data: {min_gas_threshold}')

    # Load USDC metadata
    # Load USDC metadata
    usdc_data = token_data()
    usdc_price = usdc_data.get('market_data', {}).get('current_price', {}).get('usd', 1)

    TOKEN_DECIMALS = extract_token_decimals(usdc_data)
    TOKEN_CONTRACTS = extract_token_contracts(usdc_data)
    TOKEN_CONTRACTS = to_checksum_dict(TOKEN_CONTRACTS)

    # Handle externally passed account_obj (Python SDK usage)
    if account_obj is not None:
        if isinstance(account_obj, dict):
            account_obj_list = [account_obj]
        else:
            account_obj_list = account_obj

        # Infer source_chain from Web3 context if not provided
        if source_chain is None:
            w3 = account_obj_list[0]['w3']
            chain_id = w3.eth.chain_id
            from ccip_terminal.metadata import CHAIN_MAP
            source_chain = next((k for k, v in CHAIN_MAP.items() if v["chainID"] == chain_id), None)

        # Infer account index if not provided
        if account_index is None:
            account_index = 0  # fallback
    else:
        # CLI-style usage
        if source_chain is not None:
            account_obj_list = load_accounts(network=source_chain,account_index=account_index)
        else:
            account_obj_list = load_accounts(account_index=account_index)
    
    # Get balances
    BALANCES_DICT = get_all_balances_simple(
        TOKEN_CONTRACTS,
        TOKEN_DECIMALS,
        account_obj_list,
        only_chain=source_chain
    )

    # Select account if not fully specified
    if account_obj is None:
        if source_chain is None:
            largest_balance_dict = get_largest_balance(
                BALANCES_DICT,
                account_obj_list,
                min_gas_threshold=min_gas_threshold,
                exclude_chain=dest_chain
            )

            if not largest_balance_dict.get("max_network"):
                raise RuntimeError("Unable to determine source chain: no account met gas threshold or balance criteria.")

            if account_index is None:
                account_index = largest_balance_dict.get("account_index", 0)

            source_chain = largest_balance_dict.get("max_network")

        if account_index is None:
            account_index = 0

        # Load selected account with network context
        account_data = load_accounts(network=source_chain, account_index=account_index)
        account_obj = account_data[0]  # single dict with 'account' and 'w3'


    return {
        "balances": BALANCES_DICT,
        "contracts": TOKEN_CONTRACTS,
        "decimals": TOKEN_DECIMALS,
        "account": account_obj,
        "usdc_price": usdc_price,
        "account_index": account_index,
        "source_chain": source_chain
    }

def get_all_balances_simple(TOKEN_CONTRACTS, TOKEN_DECIMALS, account_obj, only_chain=None):
    BALANCE_DICT = {}

    for obj in account_obj:
        account = obj["account"]
        address = account.address

        BALANCE_DICT[address] = {}

        for chain_name, token_address in TOKEN_CONTRACTS.items():
            if only_chain and chain_name != only_chain:
                continue

            try:
                w3_chain = network_func(chain_name)

                single_token_dict = get_balance(
                    {chain_name: token_address},
                    TOKEN_DECIMALS,
                    address,
                    w3_chain
                )

                native_balance_wei = w3_chain.eth.get_balance(address)
                native_balance_eth = w3_chain.from_wei(native_balance_wei, "ether")

                BALANCE_DICT[address][chain_name] = {
                    "usdc": single_token_dict[chain_name],
                    "native_token": float(native_balance_eth)
                }

            except Exception as e:
                print(f"Failed to fetch balances for {chain_name} / {address}: {e}")
                BALANCE_DICT[address][chain_name] = {
                    "usdc": None,
                    "native_token": None
                }

    return BALANCE_DICT

def get_usdc_data(account_index=None, get_balance_data=True, account_obj=None):
    usdc_data = token_data()
    usdc_price = (
        usdc_data.get('market_data', {})
        .get('current_price', {})
        .get('usd', 1)
    )

    TOKEN_DECIMALS = extract_token_decimals(usdc_data)
    TOKEN_CONTRACTS = extract_token_contracts(usdc_data)

    if get_balance_data:
        BALANCES_DICT, account_obj = get_all_balances(
            TOKEN_CONTRACTS,
            TOKEN_DECIMALS,
            account_index=account_index,
            account_obj=account_obj
        )
    else:
        BALANCES_DICT = None
        account_obj = None

    TOKEN_CONTRACTS = to_checksum_dict(TOKEN_CONTRACTS)

    return BALANCES_DICT, TOKEN_CONTRACTS, TOKEN_DECIMALS, account_obj, usdc_price


