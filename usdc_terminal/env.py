import os
from dotenv import load_dotenv

load_dotenv()  # loads .env in root dir by default

#Fiat onboarding api key
TRANSAK_API_KEY = os.getenv('TRANSAK_API_KEY')

#Price feed
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')

#Web3 RPCs
ALCHEMY_API_KEY = os.getenv('ALCHEMY_API_KEY')
INFURA_API_KEY = os.getenv('INFURA_API_KEY')

#Event Monitoring
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

#Notification recipient
NOTIFY_EMAIL = os.getenv('NOTIFY_EMAIL')
NOTIFY_PHONE = os.getenv('NOTIFY_PHONE')

def load_environment_variables():
    return {

        "COINGECKO_API_KEY": COINGECKO_API_KEY,

        "ALCHEMY_API_KEY": ALCHEMY_API_KEY,
        "INFURA_API_KEY": INFURA_API_KEY,

        "TRANSAK_API_KEY":TRANSAK_API_KEY,

        "ETHERSCAN_API_KEY":ETHERSCAN_API_KEY,

        "NOTIFY_EMAIL":NOTIFY_EMAIL,
        "NOTIFY_PHONE":NOTIFY_PHONE

    }
