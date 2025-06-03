#Resolve by coingecko id
# COINGECKO_MAP = {v["coingecko"]: k for k, v in CHAIN_MAP.items()}

# Resolve by chain_id
# CHAIN_ID_MAP = {v["id"]: k for k, v in CHAIN_MAP.items()}
from ccip_terminal.config import settings

NETWORK_TYPE = settings.NETWORK_TYPE
print(f"Using network type: {NETWORK_TYPE}")

if NETWORK_TYPE == 'mainnet':
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

    USDC_MAP = {
        'ethereum':'0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        'arbitrum':'0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
        'optimism':'0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85',
        'base':'0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
        'polygon':'0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359',
        'avalanche':'0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E',
    }

else:

    CHAIN_MAP = {
        "ethereum": {
            "alchemy": "eth",
            "infura": "ethereum",
            "coingecko": "ethereum",
            "aliases": ["eth"],
            "chainID": 11155111
        },
        "arbitrum": {
            "alchemy": "arb",
            "infura": "arbitrum",
            "coingecko": "arbitrum-one",
            "aliases": ["arb"],
            "chainID": 421614
        },
        "optimism": {
            "alchemy": "opt",
            "infura": "optimism",
            "coingecko": "optimistic-ethereum",
            "aliases": ["opt"],
            "chainID": 11155420
        },
        "avalanche": {
            "alchemy": "avax",
            "infura": "avalanche",
            "coingecko": "avalanche",
            "aliases": ["avax"],
            "chainID": 43113
        },
        "polygon": {
            "alchemy": "polygon",
            "infura": "polygon",
            "coingecko": "polygon-pos",
            "aliases": [],
            "chainID": 80002
        },
        "base": {
            "alchemy": "base",
            "infura": "base",
            "coingecko": "base",
            "aliases": [],
            "chainID": 84532
        }
    }

    ROUTER_MAP = {
        'arbitrum': '0x2a9C5afB0d0e4BAb2BCdaE109EC4b0c4Be15a165',
        'ethereum': '0x0BF3dE8c5D3e8A2B34D2BEeB17ABfCeBaf363A59',
        'avalanche': '0xF694E193200268f9a4868e4Aa017A0118C9a8177',
        'optimism': '0x114A20A10b43D4115e5aeef7345a1A71d2a60C57',
        'polygon': '0x9C32fCB86BF0f4a1A8921a9Fe46de3198bb884B2',
        'base': '0xD3b06cEbF099CE7DA4AcCf578aaebFDBd6e88a93'
    }

    CHAIN_SELECTORS = {
        'ethereum': 16015286601757825753,
        'arbitrum': 3478487238524512106,
        'optimism': 5224473277236331295,
        'avalanche': 14767482510784806043,
        'polygon': 16281711391670634445,
        'base': 10344971235874465080
    }

    USDC_MAP = {
        'ethereum':'0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238',
        'arbitrum':'0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d',
        'optimism':'0x5fd84259d66Cd46123540766Be93DFE6D43130D7',
        'base':'0x036CbD53842c5426634e7929541eC2318f3dCF7e',
        'polygon':'0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582',
        'avalanche':'0x5425890298aed601595a70AB815c96711a31Bc65',
    }

TOKEN_DECIMALS = {
    'ethereum': 6,
    'arbitrum': 6,
    'optimism': 6,
    'base': 6,
    'polygon': 6,
    'avalanche': 6
}

FEE_TOKEN_ADDRESS = "0x0000000000000000000000000000000000000000"

MAX_UINT256 = 2**256 - 1 

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
    'ethereum': 500_000,
    'arbitrum': 400_000,
    'optimism': 400_000,
    'base': 400_000,
    'polygon': 400_000,
    'avalanche': 400_000,
}
