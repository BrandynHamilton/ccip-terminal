from cachetools import TTLCache, cached

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3, EthereumTesterProvider
from web3.exceptions import TransactionNotFound,TimeExhausted
from web3.middleware import ExtraDataToPOAMiddleware

import math
import pandas as pd 
from functools import lru_cache

import os
import sys
from dotenv import load_dotenv

import random
import time
import json

from usdc_terminal.config import config
from usdc_terminal.metadata import CHAIN_MAP, ROUTER_MAP, MAX_UINT256, GAS_LIMITS_BY_CHAIN
from usdc_terminal.env import (ALCHEMY_API_KEY,INFURA_API_KEY)
from usdc_terminal.logger import logger
from usdc_terminal.network import resolve_chain_name

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ABI_DIR = os.path.join(BASE_DIR, 'abi')
LOG_DIR = os.path.join(BASE_DIR, 'log_data')
LOG_PATH = os.path.join(LOG_DIR, 'transfer.log')

def to_checksum_dict(d):
    """Recursively converts all address values in a dict to checksum format."""
    return {k: Web3.to_checksum_address(v) if isinstance(v, str) and v.startswith("0x") else v for k, v in d.items()}

def deep_checksum(data):
    """Recursively converts all Ethereum addresses in a nested dict, list, or tuple to checksum format."""
    if isinstance(data, dict):
        return {k: deep_checksum(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [deep_checksum(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(deep_checksum(item) for item in data)
    elif isinstance(data, str) and data.startswith("0x") and len(data) == 42:
        try:
            return Web3.to_checksum_address(data)
        except Exception:
            return data  # If it's not a valid address, leave it as is
    else:
        return data

def load_abi():
    """
    Load all ABI JSON files from the abi/ directory and return as a dictionary.
    """
    abi_files = []  # Store all ABI file paths

    # Iterate over all JSON files in the ABI directory
    for file in os.listdir(ABI_DIR):
        if file.endswith(".json"):  # Only include JSON files
            abi_files.append(os.path.join(ABI_DIR, file))

    abis = {}

    for path in abi_files:
        filename = os.path.basename(path)
        name = os.path.splitext(filename)[0]  # Remove .json extension

        with open(path, "r") as f:
            abis[name] = json.load(f)

    return abis

def clear_logs():
    with open(LOG_PATH, 'w'):
        pass
    logger.info("🧹 Logs cleared.")



def get_token_decimals(TOKEN_CONTRACTS,w3):
        
        """Fetch decimals for each token contract using Web3."""
        try:
            # ERC20 ABI for decimals function
            decimals_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                }
            ]

            # Dictionary to store decimals for each token
            token_decimals = {}

            for token, address in TOKEN_CONTRACTS.items():
                if address:
                    try:
                        contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=decimals_abi)
                        decimals = contract.functions.decimals().call()
                        token_decimals[token] = decimals
                    except Exception as e:
                        print(f"Error fetching decimals for {token}: {e}")
                        token_decimals[token] = None
                else:
                    print(f"Contract address for {token} is not set.")
                    token_decimals[token] = None

            return token_decimals

        except Exception as e:
            print(f"Error: {e}")
            return None



def convert_to_usd(balances, prices,TOKEN_CONTRACTS):
    """
    Convert token balances to their USD equivalent using token prices.

    Parameters:
    - balances (dict): Dictionary of token balances.
    - prices (dict): Dictionary of token prices.

    Returns:
    - dict: Dictionary of token balances converted to USD.
    """
    # Convert token keys to upper case for consistency
    for token in TOKEN_CONTRACTS.keys():
        if f"{token}" not in prices:
            print(f"Missing price for token: {token}")

    usd_balances = {
        token: balances[token] * prices[f"{token}"]
        for token in TOKEN_CONTRACTS.keys()
        if f"{token}" in prices
    }
    return usd_balances

def extract_token_decimals(token_data):
    token_decimals = {}
    detail_platforms = token_data.get("detail_platforms", {})

    if detail_platforms:
        for platform, platform_data in detail_platforms.items():
            try:
                network = resolve_chain_name(platform)  # normalize to canonical chain name
                decimals = platform_data.get('decimal_place', 6)
                token_decimals[network] = decimals
            except ValueError:
                # Platform not in CHAIN_MAP — skip
                continue
    else:
        # Fallback to default decimals for all chains
        token_decimals = {chain: 6 for chain in CHAIN_MAP.keys()}

    return token_decimals

def extract_token_contracts(token_data):
    token_contracts = {}

    for platform, contract_address in token_data.get("platforms", {}).items():
        try:
            network = resolve_chain_name(platform)
            token_contracts[network] = contract_address
        except ValueError:
            # Platform not supported in CHAIN_MAP
            continue

    return token_contracts

def check_ccip_lane(router, dest_selector):
    is_supported = router.functions.isChainSupported(dest_selector).call()
    if not is_supported:
        raise Exception(f"❌ No outbound lane configured to dest selector: {dest_selector}")
    print(f"✅ Destination chain selector {dest_selector} is supported")

def check_offramp(router, dest_selector):
    offramps = router.functions.getOffRamps().call()
    valid = any(o[0] == dest_selector for o in offramps)
    if not valid:
        raise Exception(f"❌ No active OffRamp for selector {dest_selector}. CCIP transfer will fail.")

def approve_token_if_needed(token_address, 
                            spender, 
                            account_obj, 
                            threshold=None):
    """Check token allowance and approve if under threshold."""
    threshold = threshold or int(MAX_UINT256 * 0.95)
    abis = load_abi()
    w3 = account_obj["w3"]
    account = account_obj["account"]
    private_key = account.key.hex()
    token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=abis['erc20_abi'])

    # 1. Check current allowance
    current_allowance = token_contract.functions.allowance(account.address, spender).call()
    print(f"Current allowance: {current_allowance}")

    if current_allowance >= threshold:
        print(f"✅ Sufficient allowance ({current_allowance}), skipping approval.")
        return True

    # 2. Build approve transaction
    nonce = w3.eth.get_transaction_count(account.address)
    approve_txn = token_contract.functions.approve(spender, MAX_UINT256).build_transaction({
        "chainId": w3.eth.chain_id,
        "nonce": nonce,
        "from": account.address 
    })

    # Get dynamic fees (EIP-1559)
    try:
        latest_block = w3.eth.get_block("latest")
        base_fee = latest_block["baseFeePerGas"]
        max_priority_fee = w3.to_wei(2, "gwei")  # Reasonable tip for Arbitrum
        max_fee_per_gas = base_fee + max_priority_fee

        print(f"Base Fee: {w3.from_wei(base_fee, 'gwei')} gwei")
        print(f"Priority Fee: {w3.from_wei(max_priority_fee, 'gwei')} gwei")
        print(f"Max Fee: {w3.from_wei(max_fee_per_gas, 'gwei')} gwei")

        # Update transaction with EIP-1559 gas settings
        approve_txn["maxFeePerGas"] = max_fee_per_gas
        approve_txn["maxPriorityFeePerGas"] = max_priority_fee

    except Exception as e:
        print(f"Failed to retrieve gas fees: {e}")
        approve_txn["maxFeePerGas"] = w3.to_wei("1.5", "gwei")
        approve_txn["maxPriorityFeePerGas"] = w3.to_wei("0.5", "gwei")

    # Optional: safer gas estimation
    try:
        gas_estimate = w3.eth.estimate_gas({
            "to": token_address,
            "from": account.address,
            "data": approve_txn["data"]
        })
        approve_txn["gas"] = gas_estimate
        print(f"Gas estimate: {gas_estimate}")
    except Exception as e:
        print(f"⚠️ Gas estimation failed: {e}")
        approve_txn["gas"] = 60000  

    # 3. Sign and send
    signed_txn = w3.eth.account.sign_transaction(approve_txn, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"🔑 Approval Transaction Sent: {tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"✅ Approval Transaction Mined: {tx_hash.hex()}")

    return receipt.status == 1

def estimate_dynamic_gas(router, dest_selector, message, account, buffer=1.2, default_gas=300_000, max_gas=1_200_000):
    """
    Dynamically estimate gas limit for CCIP transfer.
    
    Args:
        router: Web3 contract instance of the router.
        dest_selector: Destination chain selector.
        message: CCIP message object.
        account: Account address sending the tx.
        buffer: Multiplier buffer to add to estimated gas.
        max_gas: Optional maximum gas cap to avoid crazy fees.
    
    Returns:
        int: Final gas limit.
    """
    try:
        estimated = router.functions.ccipSend(dest_selector, message).estimate_gas({'from': account})
        gas_limit = int(estimated * buffer)
        if gas_limit > max_gas:
            logger.warning(f"⚠️ Gas limit estimate ({gas_limit}) exceeds max cap ({max_gas}). Using cap.")
            gas_limit = max_gas
        logger.info(f"✅ Estimated Gas: {estimated}, with buffer: {gas_limit}")
        return gas_limit
    except Exception as e:
        logger.warning(f"⚠️ Gas estimation failed, fallback used. Reason: {e}")
        return int(default_gas * buffer)

# def estimate_dynamic_gas(
#     router,
#     dest_selector,
#     message,
#     account,
#     chain_name,
#     buffer=1.2,
#     default_gas=500_000,
#     max_gas=1_200_000
# ):
#     """
#     Dynamically estimate gas limit for CCIP transfer.
    
#     Args:
#         router: Web3 contract instance of the router.
#         dest_selector: Destination chain selector.
#         message: CCIP message object.
#         account: Account address sending the tx.
#         chain_name (str): Name of the source chain (for fallback values).
#         buffer (float): Multiplier buffer to add to estimated gas.
#         max_gas (int): Optional maximum gas cap to avoid crazy fees.
    
#     Returns:
#         int: Final gas limit.
#     """

#     # Chain-specific static fallback values
#     GAS_LIMITS_BY_CHAIN = {
#         'ethereum': 500_000,
#         'arbitrum': 200_000,
#         'optimism': 200_000,
#         'base': 200_000,
#         'polygon': 250_000,
#         'avalanche': 300_000,
#     }

#     try:
#         estimated = router.functions.ccipSend(dest_selector, message).estimate_gas({'from': account})
#         gas_limit = int(estimated * buffer)
#         if gas_limit > max_gas:
#             logger.warning(f"⚠️ Gas limit estimate ({gas_limit}) exceeds max cap ({max_gas}). Using cap.")
#             gas_limit = max_gas
#         logger.info(f"✅ Estimated Gas: {estimated}, with buffer: {gas_limit}")
#         return gas_limit

#     except Exception as e:
#         fallback = GAS_LIMITS_BY_CHAIN.get(chain_name.lower(), default_gas)
#         gas_limit = int(fallback * buffer)
#         logger.warning(f"⚠️ Gas estimation failed. Using static fallback for {chain_name}: {gas_limit}. Reason: {e}")
#         return gas_limit














