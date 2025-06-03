import requests
from ccip_terminal.env import ETHERSCAN_API_KEY
from ccip_terminal.metadata import CHAIN_MAP
from eth_utils import keccak

def estimate_start_block(days_ago: int, w3) -> int:
    latest_block = w3.eth.get_block("latest")["number"]
    est_block = latest_block - (days_ago * 6500)
    return max(est_block, 0)

def estimate_gas_limit_from_recent_ccip_dev(w3, days=5, etherscan_api_key=None, max_txs=10):
    if etherscan_api_key is None:
        etherscan_api_key = ETHERSCAN_API_KEY

    topic0 = '0xd0c3c799bf9e2639de44391e7f524d229b2b55f5b1ea94b2bf7da42f7243dddd'
    chain_id = w3.eth.chain_id
    url = "https://api.etherscan.io/v2/api"
    startblock = estimate_start_block(days, w3)

    params = {
        "chainid": chain_id,
        "module": "logs",
        "action": "getLogs",
        "fromBlock": startblock,
        "toBlock": "latest",
        "topic0": topic0,
        "apikey": etherscan_api_key
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        logs = response.json().get("result", [])

        gas_limits = []
        gas_used_values = []
        receipts = []

        for log in logs[:max_txs]:
            tx_hash = log["transactionHash"]
            tx = w3.eth.get_transaction(tx_hash)
            receipt = w3.eth.get_transaction_receipt(tx_hash)

            gas_limits.append(tx["gas"])          # <-- this is the gas limit used by sender
            gas_used_values.append(receipt.gasUsed)
            receipts.append(receipt)

        if not gas_limits:
            return None

        avg_gas_limit = int(sum(gas_limits) / len(gas_limits))
        avg_gas_used = int(sum(gas_used_values) / len(gas_used_values))
        min_gas_limit = min(gas_limits)

        return avg_gas_limit, min_gas_limit, gas_used_values, receipts

    except Exception as e:
        print(f"[Error] Failed to estimate gas limit: {e}")
        return None, None, []
    

def estimate_gas_limit_from_recent_ccip(w3, days=30, etherscan_api_key=None, max_txs=10):
    if etherscan_api_key is None:
        etherscan_api_key = ETHERSCAN_API_KEY

    topic0 = '0xd0c3c799bf9e2639de44391e7f524d229b2b55f5b1ea94b2bf7da42f7243dddd'
    chain_id = w3.eth.chain_id
    url = "https://api.etherscan.io/v2/api"
    startblock = estimate_start_block(days, w3)

    params = {
        "chainid": chain_id,
        "module": "logs",
        "action": "getLogs",
        "fromBlock": startblock,
        "toBlock": "latest",
        "topic0": topic0,
        "apikey": etherscan_api_key
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        logs = response.json().get("result", [])

        gas_limits = []
        gas_used_values = []
        receipts = []

        for log in logs[:max_txs]:
            tx_hash = log["transactionHash"]
            tx = w3.eth.get_transaction(tx_hash)
            receipt = w3.eth.get_transaction_receipt(tx_hash)

            gas_limits.append(tx["gas"])          # <-- this is the gas limit used by sender
            gas_used_values.append(receipt.gasUsed)
            receipts.append(receipt)

        if not gas_limits:
            return None

        avg_gas_limit = int(sum(gas_limits) / len(gas_limits))
        avg_gas_used = int(sum(gas_used_values) / len(gas_used_values))
        min_gas_limit = min(gas_limits)

        return avg_gas_used

    except Exception as e:
        print(f"[Error] Failed to estimate gas limit: {e}")
        return None

