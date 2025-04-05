from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from functools import lru_cache
from usdc_transfer.metadata import CHAIN_MAP
from usdc_transfer.env import ALCHEMY_API_KEY, INFURA_API_KEY

@lru_cache
def build_chain_lookup():
    lookup = {}
    for chain, data in CHAIN_MAP.items():
        lookup[chain] = chain
        lookup[data["coingecko"]] = chain
        for alias in data.get("aliases", []):
            lookup[alias] = chain
    return lookup

def resolve_chain_name(name):
    lookup = build_chain_lookup()
    name = name.lower()
    if name in lookup:
        return lookup[name]
    raise ValueError(f"Unknown chain name, alias, or coingecko name: {name}")

def network_func(chain='ethereum', type='mainnet'):
    chain = chain.lower()
    chain = resolve_chain_name(chain)  # Will raise ValueError if invalid

    chain_data = CHAIN_MAP[chain]
    alchemy_key = chain_data["alchemy"]
    infura_key = chain_data["infura"]

    # Compose Gateway URLs
    ALCHEMY_GATEWAY = f"https://{alchemy_key}-{type}.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
    
    if infura_key == 'ethereum':
        INFURA_GATEWAY = f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"
    else:
        INFURA_GATEWAY = f"https://{infura_key}-{type}.infura.io/v3/{INFURA_API_KEY}"

    primary_gateway = ALCHEMY_GATEWAY
    backup_gateway = INFURA_GATEWAY

    for gateway in [primary_gateway, backup_gateway]:
        w3 = Web3(Web3.HTTPProvider(gateway))

        # Inject POA Middleware if required chains
        if chain in ["avalanche", "polygon"]:
            w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        if w3.is_connected():
            try:
                latest_block = w3.eth.get_block('latest')['number']
                print(f"✅ Connected to {chain} via {gateway}: Block {latest_block}")
                return w3
            except Exception as e:
                print(f"⚠️ Connected but failed to fetch block. Error: {e}")
        else:
            print(f"❌ Failed to connect to {chain} via {gateway}. Trying next...")

    raise ConnectionError(f"❌ Failed to connect to {chain} using both Alchemy and Infura.")