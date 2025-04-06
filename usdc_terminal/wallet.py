import os
import json
import click
from eth_account import Account
from getpass import getpass
from cryptography.fernet import Fernet
from usdc_terminal.utils import logger

KEYSTORE_FILE = "wallet_keystore.json"
ENV_FILE = ".env"


def generate_wallet():
    """Generate a new Ethereum wallet and return private key + address."""
    acct = Account.create()
    return acct.key.hex(), acct.address


def save_to_env(private_key):
    """Insecurely save the private key to .env."""
    with open(ENV_FILE, "a") as f:
        f.write(f"\nPRIVATE_KEY={private_key}\n")
    logger.warning("⚠️ Private key saved to .env (Not Recommended)")


def encrypt_keystore(private_key, password):
    """Encrypt private key to keystore JSON."""
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted_pk = f.encrypt(private_key.encode())

    data = {
        "encrypted_private_key": encrypted_pk.decode(),
        "encryption_key": key.decode()
    }

    with open(KEYSTORE_FILE, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"🔒 Keystore saved to {KEYSTORE_FILE}")


@click.command()
@click.option('--insecure-save', is_flag=True, help="Save private key to .env file (Not recommended).")
@click.option('--encrypt', is_flag=True, help="Encrypt private key and save to wallet_keystore.json.")
def create_wallet(insecure_save, encrypt):
    """Create a new Ethereum wallet."""
    private_key, address = generate_wallet()
    click.echo(f"\n🎯 Wallet Address: {address}")
    click.echo(f"🔑 Private Key: {private_key}")
    click.echo("\n📌 IMPORTANT: Back up your private key safely.")

    if insecure_save:
        save_to_env(private_key)

    if encrypt:
        password = getpass("🔐 Enter password for keystore encryption: ")
        encrypt_keystore(private_key, password)

    click.echo("\n✅ Wallet setup complete.")


if __name__ == "__main__":
    create_wallet()
