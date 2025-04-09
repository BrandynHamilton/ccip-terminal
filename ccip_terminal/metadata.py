#Resolve by coingecko id
# COINGECKO_MAP = {v["coingecko"]: k for k, v in CHAIN_MAP.items()}

# Resolve by chain_id
# CHAIN_ID_MAP = {v["id"]: k for k, v in CHAIN_MAP.items()}

CHAIN_MAP = {
    "ethereum": {
        "alchemy": "eth",
        "infura": "ethereum",
        "coingecko": "ethereum",
        "aliases": ["eth"],
        "chainID": 1
    },
    "arbitrum": {
        "alchemy": "arb",
        "infura": "arbitrum",
        "coingecko": "arbitrum-one",
        "aliases": ["arb"],
        "chainID": 42161
    },
    "optimism": {
        "alchemy": "opt",
        "infura": "optimism",
        "coingecko": "optimistic-ethereum",
        "aliases": ["opt"],
        "chainID": 10
    },
    "avalanche": {
        "alchemy": "avax",
        "infura": "avalanche",
        "coingecko": "avalanche",
        "aliases": ["avax"],
        "chainID": 43114
    },
    "polygon": {
        "alchemy": "polygon",
        "infura": "polygon",
        "coingecko": "polygon-pos",
        "aliases": [],
        "chainID": 137
    },
    "base": {
        "alchemy": "base",
        "infura": "base",
        "coingecko": "base",
        "aliases": [],
        "chainID": 8453
    }
}

ROUTER_MAP = {
    'arbitrum': '0x141fa059441E0ca23ce184B6A78bafD2A517DdE8',
    'ethereum': '0x80226fc0Ee2b096224EeAc085Bb9a8cba1146f7D',
    'avalanche': '0xF4c7E640EdA248ef95972845a62bdC74237805dB',
    'optimism': '0x3206695CaE29952f4b0c22a169725a865bc8Ce0f',
    'polygon': '0x849c5ED5a80F5B408Dd4969b78c2C8fdf0565Bfe',
    'base': '0x881e3A65B4d4a04dD529061dd0071cf975F58bCD'
}

CHAIN_SELECTORS = {
    'ethereum': 5009297550715157269,
    'arbitrum': 4949039107694359620,
    'optimism': 3734403246176062136,
    'avalanche': 6433500567565415381,
    'polygon': 4051577828743386545,
    'base': 15971525489660198786
}

# Fallback metadata for transak
FALLBACK_GAS_TOKENS = {
    "ethereum": "ETH",
    "arbitrum": "ETH",
    "optimism": "ETH",
    "polygon": "MATIC",
    "avalanche": "AVAX",
    "base": "ETH"
}

GAS_LIMITS_BY_CHAIN = {
    'ethereum': 300_000,
    'arbitrum': 300_000,
    'optimism': 250_000,
    'base': 250_000,
    'polygon': 250_000,
    'avalanche': 250_000,
}

FEE_TOKEN_ADDRESS = "0x0000000000000000000000000000000000000000"

MAX_UINT256 = 2**256 - 1 
