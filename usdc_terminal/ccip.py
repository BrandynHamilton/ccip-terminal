from web3 import Web3
import time
import requests

from eth_account import Account
from eth_abi import encode
from eth_utils import keccak, to_checksum_address
from usdc_terminal.utils import load_abi, logger, approve_token_if_needed, check_ccip_lane, estimate_dynamic_gas
from usdc_terminal.accounts import load_accounts
from usdc_terminal.env import ETHERSCAN_API_KEY
from usdc_terminal.account_state import get_usdc_data
from usdc_terminal.metadata import (CHAIN_MAP, FEE_TOKEN_ADDRESS, 
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
    print(f"extraArgs: {extra_args_encoded.hex()}")

    # Correctly build the message dict (Solidity struct)
    message = {
        "receiver": encode(['address'], [to_checksum_address(receiver)]),
        "data": b'',
        "tokenAmounts": [{"token": to_checksum_address(token_address), "amount": amount_wei}],
        "feeToken": to_checksum_address(fee_token),
        "extraArgs": extra_args_encoded
    }
    return message

def send_ccip_transfer(to_address, dest_chain, amount,
                       source_chain='arbitrum', account_index=0, tx_type=2):
    # === Setup ===
    BALANCES_DICT, TOKEN_CONTRACTS, TOKEN_DECIMALS = get_usdc_data()
    account_obj = load_accounts(source_chain)[account_index]
    w3 = account_obj["w3"]
    account = account_obj["account"]
    router_address = resolve_router_address(source_chain)
    router = w3.eth.contract(address=router_address, abi=ROUTER_ABI)
    token_address = TOKEN_CONTRACTS[source_chain]
    token_decimals = TOKEN_DECIMALS[source_chain]

    # === Check balance of token ===
    erc20 = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=abis["erc20_abi"])
    token_balance = erc20.functions.balanceOf(account.address).call()
    required_amount = int(amount * (10 ** token_decimals))
    print(f'token_balance: {token_balance}')
    print(f'required_amount: {required_amount}')
    if token_balance < required_amount:
        raise Exception(f"❌ Insufficient {source_chain.upper()} USDC balance. Have: {token_balance}, Need: {required_amount}")

    # === Approve if needed ===
    approve_token_if_needed(token_address, router_address, account_obj, threshold=None)

    # === Build CCIP Message ===
    dest_selector = resolve_chain_selector(dest_chain)
    check_ccip_lane(router, dest_selector)

    message = build_ccip_message(
        receiver=to_address,
        token_address=token_address,
        token_decimals=token_decimals,
        amount=amount,
        fee_token=FEE_TOKEN_ADDRESS
    )

    # === Estimate Fee & Gas ===
    raw_fee = router.functions.getFee(dest_selector, message).call()
    fee = int(raw_fee * 1.1)  # Add 10% buffer

    print(f'raw_fee: {raw_fee}')
    print(f'fee: {fee}')

    gas_limit = estimate_dynamic_gas(source_chain)

    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", 0)
    max_priority_fee = w3.to_wei(2, "gwei")
    max_fee_per_gas = base_fee + max_priority_fee
    gas_price = w3.eth.gas_price

    estimated_cost = fee + (gas_limit * (max_fee_per_gas if tx_type == 2 else gas_price))
    native_balance = w3.eth.get_balance(account.address)

    print(f"native_balance: {w3.from_wei(native_balance, 'ether')} ETH")
    print(f"Estimates → Fee: {w3.from_wei(fee, 'ether')} ETH, Gas Limit: {gas_limit}, Max Fee: {w3.from_wei(max_fee_per_gas, 'gwei')} gwei")
    print(f"Total Estimated Cost: {w3.from_wei(estimated_cost, 'ether')} ETH")

    if native_balance < estimated_cost:
        raise Exception(f"❌ Insufficient native gas token balance on {source_chain}. Have: {w3.from_wei(native_balance, 'ether')} - Need: {w3.from_wei(estimated_cost, 'ether')}")

    # === Build & Send Transaction ===
    nonce = w3.eth.get_transaction_count(account.address)

    try:
        tx_params = {
            'from': account.address,
            'nonce': nonce,
            'value': fee,
            'gas': gas_limit,
            'chainId': w3.eth.chain_id,
        }
        if tx_type == 2:
            tx_params.update({
                'maxFeePerGas': max_fee_per_gas,
                'maxPriorityFeePerGas': max_priority_fee,
            })
        else:
            tx_params.update({'gasPrice': gas_price})

        message_id = None
        try:
            message_id = router.functions.ccipSend(dest_selector, message).call({
                'from': account.address,
                'value': fee
            })
            logger.info(f"CCIP messageId (pre-send): {message_id.hex()}")
        except Exception as e:
            logger.warning(f"Could not prefetch CCIP messageId: {e}")

        tx = router.functions.ccipSend(dest_selector, message).build_transaction(tx_params)
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        url = f'https://ccip-bradford-solana-streams-chainlinklabs.vercel.app/tx/0x{tx_hash.hex()}'
        if receipt.status == 1:
            logger.info(f"CCIP Transfer submitted (Type {tx_type}): {tx_hash.hex()} | View: {url}")
        else:
            logger.warning(f"CCIP Transfer {tx_hash.hex()} was mined but failed (status=0). Investigate. | View: {url}")
        return receipt, message_id.hex() if message_id else None

    except Exception as e:
        if tx_type == 2:
            logger.info(f"EIP-1559 Transaction Failed: {e}. Retrying with Legacy Type 0...")
            return send_ccip_transfer(TOKEN_CONTRACTS, TOKEN_DECIMALS, to_address, dest_chain, amount,
                                      source_chain, account_index, tx_type=0)
        else:
            logger.info(f"Legacy Transaction Failed: {e}")
            raise

def check_ccip_message_status(message_id_hex, dest_chain, wait=False, poll_interval=120, max_retries=15):
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
            "apikey": ETHERSCAN_API_KEY
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

                print(f"✅ Found status for message {message_id_hex} on {offramp_address}: {status_str}")
                return status_str, offramp_address

        except Exception as e:
            print(f"⚠️ Etherscan error: {e}")

        if not wait:
            print(f"❗ No status yet for message {message_id_hex}")
            return "NOT_FOUND", None

        attempts += 1
        if attempts >= max_retries:
            print(f"⏱️ Max retries reached for message {message_id_hex}")
            return "NOT_FOUND", None

        print(f"⏳ Attempt {attempts}/{max_retries} – retrying in {poll_interval}s...")
        time.sleep(poll_interval)

def get_ccip_fee_api(to_address,source_chain,dest_chain,amount,account_index=0,tx_type=2):

    account_obj = load_accounts(source_chain)[account_index]
    w3 = account_obj["w3"]
    account = account_obj["account"]
    router_address = resolve_router_address(source_chain)
    router = w3.eth.contract(address=router_address, abi=ROUTER_ABI)
    token_address = TOKEN_CONTRACTS[source_chain]
    token_decimals = TOKEN_DECIMALS[source_chain]

    BALANCES_DICT, TOKEN_CONTRACTS, TOKEN_DECIMALS = get_usdc_data()

    dest_selector = resolve_chain_selector(dest_chain)
    check_ccip_lane(router, dest_selector)

    message = build_ccip_message(
        receiver=to_address,
        token_address=token_address,
        token_decimals=token_decimals,
        amount=amount,
        fee_token=FEE_TOKEN_ADDRESS
    )

    # === Estimate Fee & Gas ===
    raw_fee = router.functions.getFee(dest_selector, message).call()

    gas_limit = estimate_dynamic_gas(router, dest_selector, message, account.address)

    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", 0)
    max_priority_fee = w3.to_wei(2, "gwei")
    max_fee_per_gas = base_fee + max_priority_fee
    gas_price = w3.eth.gas_price

    estimated_cost = raw_fee + (gas_limit * (max_fee_per_gas if tx_type == 2 else gas_price))
    return estimated_cost