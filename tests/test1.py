# Imports and Environment Variables

from ccip_terminal import (network_func, get_ccip_fee_estimate, approve_token_if_needed,
                           send_ccip_transfer, check_ccip_message_status, get_usdc_data,USDC_MAP,
                           ROUTER_MAP,get_largest_balance,token_data,extract_token_contracts,extract_token_decimals)
import json
from web3 import Web3
import os
from dotenv import load_dotenv

def main(network = 'arbitrum', dest_chain='base',amount=0.4):
    network = 'arbitrum' # Can set to variety of networks

    w3 = network_func(network)
    account = w3.eth.account.from_key(PRIVATE_KEY)
    account_obj={"account": account, "w3": w3}

    # %% [markdown]
    # # Sending a CCIP Transfer

    # %%
    usdc_data = token_data()
    usdc_data

    # %%
    TOKEN_DECIMALS = extract_token_decimals(usdc_data)
    TOKEN_CONTRACTS = extract_token_contracts(usdc_data)

    # %%
    TOKEN_CONTRACTS = extract_token_contracts(usdc_data)
    TOKEN_CONTRACTS

    # %%
    USDC_MAP

    # %%
    BALANCES_DICT, TOKEN_CONTRACTS, TOKEN_DECIMALS, _, usdc_price = get_usdc_data(account_obj=account_obj)
    # USDC Balance for Account Across Supported Networks

    print(json.dumps(BALANCES_DICT, indent=2))

    # %%
    largest_balance_dict = get_largest_balance(BALANCES_DICT, account_obj=account_obj,min_gas_threshold=0.003)

    # %%
    to_address = '0x2083b0413869f7b5b9e0eA27d20CB6dD3535f525'
    dest_chain='base'
    amount=0.4
    source_chain=network

    # %%
    TOKEN_CONTRACTS

    # %%
    source_chain_state = BALANCES_DICT[account.address][source_chain]
    source_chain_state['usdc']
    usdc_balance = source_chain_state['usdc']
    sufficient_token = amount <= usdc_balance

    if not sufficient_token:
        print(f'Token balance below desired send amount - Account: {usdc_balance}, Desired amount: {amount}')
    else:
        print(f'Token balance is sufficient for send amount')

    # %%
    # We need to use custom fee estimation function for CCIP

    estimate = get_ccip_fee_estimate(
        to_address=to_address,
        dest_chain=dest_chain,
        amount=amount,
        source_chain=source_chain,
        account_obj=account_obj
    )
    native_balance = w3.eth.get_balance(account.address)
    total_estimate = estimate["total_estimate"]

    print(f'native gas balance: {native_balance / 1e18}')
    print(f'gas estimate: {total_estimate / 1e18}')

    can_transfer = native_balance > total_estimate

    print(f'Enough gas for transfer?: {"yes" if can_transfer else "no"}')

    # %%
    # Note fee is overestimated as we cannot directly estimate gas. For L2 transfers, fee typically ~0.00018 or $0.24

    estimate # Denominated in wei

    # %%
    #Approves Router to Spend Our Token If Necessary

    approve_token_if_needed(TOKEN_CONTRACTS[source_chain], 
                                ROUTER_MAP[source_chain], 
                                account_obj, 
                                threshold=None)

    # %%
    receipt = None

    if can_transfer and sufficient_token:
        receipt, links, success, message_id = send_ccip_transfer(
            to_address=to_address,
            dest_chain=dest_chain,
            amount=amount,
            source_chain=source_chain,
            account_obj=account_obj,
            estimate=estimate["total_estimate"]
        )
    else:
        missing_gas = estimate["total_estimate"] - native_balance
        missing_token = amount - usdc_balance 
        print(f'Need to top up on gas; need {missing_gas / 1e18} more native token')
        print(f'May need more USDC in account or need to lower desired send amount: {missing_token}')


    # %%
    if receipt and receipt.status == 1:
        print(f'Tx Links:{links}')
        print(f'CCIP MessageID: {message_id}')
        # Here we query Etherscan for transfer status, can take up to 25 minutes.
        # Wait flag periodically calls the API for status
        check_ccip_message_status(message_id, dest_chain, wait=True)
    else:
        print(F'No Tx Detected or Tx Failed')

    return "Done"

global PRIVATE_KEY

if __name__ == "__main__":
    print("Running main function...")
    load_dotenv()

    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    if not PRIVATE_KEY:
        raise ValueError("Please set the PRIVATE_KEY environment variable.")
    main()

