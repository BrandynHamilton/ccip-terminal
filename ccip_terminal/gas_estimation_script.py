import requests
from ccip_terminal.env import ETHERSCAN_API_KEY
from ccip_terminal.metadata import CHAIN_MAP
from eth_utils import keccak

def estimate_start_block(days_ago: int, w3) -> int:
    latest_block = w3.eth.get_block("latest")["number"]
    est_block = latest_block - (days_ago * 6500)
    return max(est_block, 0)

def estimate_gas_limit_from_recent_ccip(w3, etherscan_api_key=None, max_txs=10):
    if etherscan_api_key is None:
        etherscan_api_key = ETHERSCAN_API_KEY

    signature = "CCIPSendRequested((bytes32,uint64,address,address,address,bytes,bytes,bytes,uint256,uint256,address))"
    topic0_raw = keccak(text=signature).hex()
    print(f'topic0_raw: {topic0_raw}')
    fixed_topic0_raw = '0x'+topic0_raw
    print(f'fixed topic0_raw: {fixed_topic0_raw}')
    topic0 = '0xd0c3c799bf9e2639de44391e7f524d229b2b55f5b1ea94b2bf7da42f7243dddd'
    print(f'static topic0: {topic0}')
        
    chain_id = w3.eth.chain_id

    url = "https://api.etherscan.io/v2/api"

    startblock = estimate_start_block(5, w3)  # ~5 days ago

    params = {
        "chainid": chain_id,
        "module": "logs",
        "action": "getLogs",
        "fromBlock": startblock,
        "toBlock": "latest",
        "topic0": topic0,
        "apikey": ETHERSCAN_API_KEY
    }

    print(f'startblock: {startblock}')
    print(f'params: {params}')

    response = requests.get(url, params=params, timeout=10)
    result = response.json()

    print(f'result: {result}')

    try:
        logs = result.get("result", [])
        print(f'logs: {logs}')

        gas_used_values = []

        for log in logs[:max_txs]:
            tx_hash = log["transactionHash"]
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            gas_used_values.append(receipt.gasUsed)

        if not gas_used_values:
            return None

        avg_gas = int(sum(gas_used_values) / len(gas_used_values))
        return avg_gas

    except Exception as e:
        print(f"[Error] Failed to estimate gas: {e}")
        return None
