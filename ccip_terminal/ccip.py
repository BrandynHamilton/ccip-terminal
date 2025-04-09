from web3 import Web3
import time
import requests

from eth_account import Account
from eth_abi import encode
from eth_utils import keccak, to_checksum_address
from ccip_terminal.utils import (load_abi, logger, approve_token_if_needed, check_ccip_lane, 
                                 estimate_dynamic_gas, calculate_usd_values,get_largest_balance,
                                 get_dynamic_gas_fees,generate_explorer_links)
from ccip_terminal.accounts import load_accounts
from ccip_terminal.env import ETHERSCAN_API_KEY
from ccip_terminal.account_state import prepare_transfer_data, get_usdc_data
from ccip_terminal.metadata import (CHAIN_MAP, FEE_TOKEN_ADDRESS, 
                                    CHAIN_SELECTORS, ROUTER_MAP)

abis = load_abi()
ROUTER_ABI = abis['ccip_router_abi']

def resolve_chain_selector(chain):
    return CHAIN_SELECTORS.get(chain)

def resolve_router_address(network):
    return ROUTER_MAP.get(network)

def build_ccip_message(receiver, token_address, amount, token_decimals, 
                       fee_token, gas_limit=200_000):
    amount_wei = int(amount * (10 ** token_decimals))
    evm_extra_args_v1_tag = keccak(text="CCIP EVMExtraArgsV1")[:4]
    extra_args = encode(['uint256'], [gas_limit])
    extra_args_encoded = evm_extra_args_v1_tag + extra_args

    # Correctly build the message dict (Solidity struct)
    message = {
        "receiver": encode(['address'], [to_checksum_address(receiver)]),
        "data": b'',
        "tokenAmounts": [{"token": to_checksum_address(token_address), "amount": amount_wei}],
        "feeToken": to_checksum_address(fee_token),
        "extraArgs": extra_args_encoded
    }
    return message

def get_account_info(account_index=None,min_gas_threshold=0):
    BALANCES_DICT_RAW, TOKEN_CONTRACTS, TOKEN_DECIMALS, account_obj, usdc_price = get_usdc_data(account_index=account_index)
    BALANCES_DICT = calculate_usd_values(BALANCES_DICT_RAW,usdc_price)

    largest_balance_dict = get_largest_balance(BALANCES_DICT_RAW, account_obj=account_obj,min_gas_threshold=min_gas_threshold)

    BALANCES_DICT['largest_balance_dict'] = largest_balance_dict or {}

    return BALANCES_DICT

def send_ccip_transfer(to_address, dest_chain, amount,
                       source_chain=None, account_index=None,
                       tx_type=2, estimate=None, account_obj=None):
    w3 = None
    account = None

    if account_obj:
        w3 = account_obj["w3"]
        account = account_obj["account"]
        chain_id = w3.eth.chain_id
        source_chain = next((k for k, v in CHAIN_MAP.items() if v["chainID"] == chain_id), source_chain)
        TOKEN_CONTRACTS, TOKEN_DECIMALS = get_usdc_data(get_balance_data=False)[1:3]

    # === Estimate gas + fee if not provided ===
    if estimate is None and source_chain is None:
        print(f'getting estimate')
        print(f'source_chain: {source_chain}')
        estimate = get_ccip_fee_estimate(
            to_address, dest_chain, amount,
            source_chain=source_chain,
            account_index=account_index,
            tx_type=tx_type,
            min_gas_threshold=0.003,
            w3=w3,
            account=account
        )
        estimate = estimate['total_estimate'] / 1e18

    # === Prepare account + token data ===
    if account_obj is None:
        print(f'getting transfer data in send ccip transfer')
        print(f'source_chain: {source_chain}')
        transfer_data = prepare_transfer_data(
            dest_chain=dest_chain,
            source_chain=source_chain,
            account_index=account_index,
            min_gas_threshold=estimate
        )
        account_obj = transfer_data["account"]
        source_chain = transfer_data["source_chain"]
        account_index = transfer_data["account_index"]
        TOKEN_CONTRACTS = transfer_data["contracts"]
        TOKEN_DECIMALS = transfer_data["decimals"]
        account = account_obj["account"]
        w3 = account_obj["w3"]
        print(f'source_chain after prepare transfer data in send ccip transfer: {source_chain}')

    router_address = resolve_router_address(source_chain)
    router = w3.eth.contract(address=router_address, abi=ROUTER_ABI)
    token_address = TOKEN_CONTRACTS[source_chain]
    token_decimals = TOKEN_DECIMALS[source_chain]

    # === Balance check ===
    erc20 = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=abis["erc20_abi"])
    token_balance = erc20.functions.balanceOf(Web3.to_checksum_address(account.address)).call()
    required_amount = int(amount * (10 ** token_decimals))

    if token_balance < required_amount:
        raise Exception(f"Insufficient {source_chain.upper()} USDC balance. Have: {token_balance}, Need: {required_amount}")

    # === Approve router ===
    approve_token_if_needed(token_address, router_address, account_obj, threshold=None)

    # === Build message ===
    dest_selector = resolve_chain_selector(dest_chain)
    check_ccip_lane(router, dest_selector)

    message = build_ccip_message(
        receiver=to_address,
        token_address=token_address,
        token_decimals=token_decimals,
        amount=amount,
        fee_token=FEE_TOKEN_ADDRESS
    )

    # === Fee + Gas estimation ===
    raw_fee = router.functions.getFee(dest_selector, message).call()
    fee = int(raw_fee * 1.1)

    gas_limit = estimate_dynamic_gas(source_chain)
    fees = get_dynamic_gas_fees(w3)

    max_fee_per_gas = fees["max_fee_per_gas"]
    max_priority = fees["max_priority_fee"]
    gas_price = fees["gas_price"]

    estimated_cost = fee + gas_limit * (max_fee_per_gas if tx_type == 2 else gas_price)
    native_balance = w3.eth.get_balance(account.address)

    if native_balance < estimated_cost:
        raise Exception(
            f"Insufficient native gas token balance on {source_chain}. "
            f"Have: {w3.from_wei(native_balance, 'ether')} - Need: {w3.from_wei(estimated_cost, 'ether')}"
        )

    # === Build + Send TX ===
    nonce = w3.eth.get_transaction_count(account.address)
    tx_params = {
        "from": account.address,
        "nonce": nonce,
        "value": fee,
        "gas": gas_limit,
        "chainId": w3.eth.chain_id,
    }

    if tx_type == 2:
        tx_params.update({
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": max_priority,
        })
    else:
        tx_params.update({"gasPrice": gas_price})

    message_id = None
    try:
        try:
            message_id = router.functions.ccipSend(dest_selector, message).call({
                "from": account.address,
                "value": fee
            })
            logger.info(f"CCIP messageId (pre-send): {message_id.hex()}")
        except Exception as e:
            logger.warning(f"Could not prefetch CCIP messageId: {e}")

        tx = router.functions.ccipSend(dest_selector, message).build_transaction(tx_params)
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        links = generate_explorer_links(source_chain, tx_hash, message_id.hex() if message_id else None)
        success = receipt.status == 1

        if not success:
            logger.warning(f"TX {tx_hash.hex()} mined but failed. Check: {links['source_url']}")
            try:
                failed_tx = w3.eth.get_transaction(tx_hash)
                w3.eth.call(failed_tx, block_identifier=receipt.blockNumber)
            except Exception as revert_e:
                print(f"↪Revert reason: {revert_e}")

        return receipt, links, success, message_id.hex() if message_id else None

    except Exception as e:
        if tx_type == 2:
            logger.info(f"EIP-1559 tx failed: {e}. Retrying legacy (Type 0)...")
            return send_ccip_transfer(
                to_address=to_address,
                dest_chain=dest_chain,
                amount=amount,
                source_chain=source_chain,
                account_index=account_index,
                tx_type=0,
                account_obj=account_obj,
                estimate=estimate
            )
        else:
            logger.error(f"Legacy tx failed: {e}")
            raise

def check_ccip_message_status(message_id_hex, dest_chain, wait=False, poll_interval=120, max_retries=15,etherscan_key=None):
    """
    Query Etherscan to detect when an OffRamp emits a status event for a given CCIP message ID.

    Args:
        message_id_hex (str): Message ID (32 bytes, hex string).
        dest_chain (str): Destination chain name.
        wait (bool): Whether to poll until the message is found.
        poll_interval (int): Time between polling attempts in seconds.
        max_retries (int): Maximum number of retries if wait=True.

    Returns:
        tuple: (status_str, address) or ("NOT_FOUND", None)
    """
    if not etherscan_key:
        etherscan_key = ETHERSCAN_API_KEY

    topic2 = '0x' + message_id_hex.lower()
    event_signature_str = "ExecutionStateChanged(uint64,bytes32,uint8,bytes)"
    topic0 = '0x' + keccak(text=event_signature_str).hex()

    status_map = {
        0: "UNTOUCHED",
        1: "IN_PROGRESS",
        2: "SUCCESS",
        3: "FAILURE"
    }

    chain_id = CHAIN_MAP.get(dest_chain, {}).get("chainID")
    if not chain_id:
        raise ValueError(f"❌ No chainID found for {dest_chain}")

    url = "https://api.etherscan.io/v2/api"
    attempts = 0

    while True:
        params = {
            "chainid": chain_id,
            "module": "logs",
            "action": "getLogs",
            "fromBlock": 0,
            "toBlock": "latest",
            "topic0": topic0,
            "topic2": topic2,
            "apikey": etherscan_key
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            data = response.json()

            if data.get("status") == "1" and data.get("result"):
                log = data["result"][0]
                offramp_address = log["address"]
                state_hex = log["data"][2:66]
                state = int(state_hex, 16)
                status_str = status_map.get(state, "UNKNOWN")

                print(f"Found status for message {message_id_hex} on {offramp_address}: {status_str}")
                return status_str, offramp_address

        except Exception as e:
            print(f"Etherscan error: {e}")

        if not wait:
            print(f"No status yet for message {message_id_hex}")
            return "NOT_FOUND", None

        attempts += 1
        if attempts >= max_retries:
            print(f"Max retries reached for message {message_id_hex}")
            return "NOT_FOUND", None

        print(f"Attempt {attempts}/{max_retries} – retrying in {poll_interval}s...")
        time.sleep(poll_interval)

def get_ccip_fee_estimate(
    to_address,
    dest_chain,
    amount,
    source_chain=None,
    account_index=None,
    tx_type=2,
    min_gas_threshold=0.003,
    w3=None,
    account=None
):
    if not w3 or not account:
        print(f'at estimate getting transfer data')
        transfer_data = prepare_transfer_data(
            dest_chain=dest_chain,
            source_chain=source_chain,
            account_index=account_index,
            min_gas_threshold=min_gas_threshold
        )
        BALANCES_DICT_RAW = transfer_data["balances"]
        TOKEN_CONTRACTS = transfer_data["contracts"]
        TOKEN_DECIMALS = transfer_data["decimals"]
        account_obj = transfer_data["account"]
        usdc_price = transfer_data["usdc_price"]
        account_index = transfer_data["account_index"]
        source_chain = transfer_data["source_chain"]
        account = account_obj["account"]
        w3 = account_obj["w3"]
    else:
        # If w3/account provided directly, we still need metadata
        from ccip_terminal.metadata import CHAIN_SELECTORS, ROUTER_MAP
        from ccip_terminal.account_state import token_data, extract_token_contracts, extract_token_decimals, to_checksum_dict
        print(f'Getting token data')
        usdc_data = token_data()
        TOKEN_DECIMALS = extract_token_decimals(usdc_data)
        TOKEN_CONTRACTS = to_checksum_dict(extract_token_contracts(usdc_data))
        usdc_price = usdc_data.get('market_data', {}).get('current_price', {}).get('usd', 1)

    router_address = resolve_router_address(source_chain)
    router = w3.eth.contract(address=router_address, abi=ROUTER_ABI)
    token_address = TOKEN_CONTRACTS[source_chain]
    token_decimals = TOKEN_DECIMALS[source_chain]

    dest_selector = resolve_chain_selector(dest_chain)
    check_ccip_lane(router, dest_selector)

    message = build_ccip_message(
        receiver=to_address,
        token_address=token_address,
        token_decimals=token_decimals,
        amount=amount,
        fee_token=FEE_TOKEN_ADDRESS
    )

    raw_fee = router.functions.getFee(dest_selector, message).call()
    fee = int(raw_fee * 1.1)  # 10% buffer

    gas_limit = estimate_dynamic_gas(source_chain)
    fees = get_dynamic_gas_fees(w3)

    gas_fee = gas_limit * (fees['max_fee_per_gas'] if tx_type == 2 else fees['gas_price'])
    total = fee + gas_fee

    return {
        "total_estimate": total,
        "native_gas_fee": gas_fee,
        "ccip_fee": fee,
        "gas_limit": gas_limit,
        "max_fee_per_gas": fees['max_fee_per_gas'],
        "priority_fee": fees['max_priority_fee'],
        "base_gas_price": fees['gas_price'],
        "currency": w3.eth.chain_id,
    }

