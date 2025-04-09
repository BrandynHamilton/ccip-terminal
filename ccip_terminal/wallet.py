import os
import json
import click
from eth_account import Account
from getpass import getpass
from cryptography.fernet import Fernet
from ccip_terminal.utils import logger

ENV_FILE = ".env"

def generate_wallet():
    """Generate a new Ethereum wallet and return private key + address."""
    acct = Account.create()
    return acct.key.hex(), acct.address


def save_to_env(private_key):
    """Insecurely save the private key to .env."""
    with open(ENV_FILE, "a") as f:
        f.write(f"\nPRIVATE_KEYS={private_key}\n")
    logger.warning("Private key saved to .env (Not Recommended)")

def encrypt_keystore(private_key, password, output_file="wallet_keystore.json"):
    key = Fernet.generate_key()
    cipher = Fernet(key)
    encrypted_key = cipher.encrypt(private_key.encode())

    with open(output_file, "w") as f:
        json.dump({
            "encrypted_key": encrypted_key.decode(),
            "fernet_key": key.decode()
        }, f)

def decrypt_keystore(password, keystore_file="wallet_keystore.json"):
    with open(keystore_file, "r") as f:
        data = json.load(f)

    cipher = Fernet(data["fernet_key"].encode())
    decrypted_key = cipher.decrypt(data["encrypted_key"].encode())
    return decrypted_key.decode()


