import os
import json
import click
from getpass import getpass
from cryptography.fernet import Fernet

from ccip_terminal.core import batch_transfer
from ccip_terminal.ccip import send_ccip_transfer, get_account_info, get_ccip_fee_estimate, check_ccip_message_status
from ccip_terminal.notifications import send_email_notification
from ccip_terminal.logger import logger
from ccip_terminal.wallet import generate_wallet, save_to_env, encrypt_keystore

from fiat_ramps import create_transak_session, run_webhook_server
from scheduler import schedule_ccip_transfer, start_scheduler_server

import sys
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

ADDRESS_BOOK_FILE = "data/address_book.json"

def load_address_book():
    if not os.path.exists(ADDRESS_BOOK_FILE):
        return {}
    with open(ADDRESS_BOOK_FILE) as f:
        return json.load(f)

def save_address_book(book):
    with open(ADDRESS_BOOK_FILE, "w") as f:
        json.dump(book, f, indent=2)

@click.group()
def cli():
    """USDC Transfer CLI"""
    pass

# UTILITY COMMAND 
@cli.command()
@click.option('--network', default='ethereum', help='Blockchain network to use.')
def show_accounts(network):
    """Display all available wallet addresses and their indexes."""
    from ccip_terminal.accounts import load_accounts

    accounts = load_accounts(network=network)
    for idx, obj in enumerate(accounts):
        print(f"[{idx}] {obj['account'].address}")

# ACCOUNT INFO COMMAND
@cli.command()
@click.option('--account_index', default=None, type=int)
@click.option('--min-gas-threshold', default=0)
def get_account_status(account_index, min_gas_threshold):
    account_info = get_account_info(account_index,min_gas_threshold)
    logger.info(f'Account Data: {json.dumps(account_info, indent=2)}')
    logger.info(f"Largest Balance Info: {account_info['largest_balance_dict']}")

# ESTIMATE GAS COST
@cli.command()
@click.option('--to', help='Destination wallet address.')
@click.option('--dest', help='Destination chain.')
@click.option('--amount', type=float, help='Amount to send.')
@click.option('--source', default=None, type=str, help='Source chain.')
@click.option('--account-index', default=None, type=int, help='Account index to use.')
@click.option('--tx-type', default=2, type=int, help='Select EIP 1559 Tx (2) or Legacy 2 (0)')
@click.option('--min-gas', default=0.001, type=float, help='Minimum Gas Required Denominated in Fee Token')
def estimate_gas_cost(to, dest, amount, source, account_index, tx_type, min_gas):
    estimate =  get_ccip_fee_estimate(to, dest, amount,
                          source_chain=source, account_index=account_index, 
                          tx_type=tx_type, min_gas_threshold=min_gas)
    print(estimate["total_estimate"] / 1e18, "ETH estimated")

# 🚀 TRANSFER COMMAND
@cli.command()
@click.option('--to', help='Destination wallet address.')
@click.option('--dest', help='Destination chain.')
@click.option('--amount', type=float, help='Amount to send.')
@click.option('--source', default=None, type=str, help='Source chain.')
@click.option('--batch-file', type=click.Path(), help='Path to batch JSON or CSV file.')
@click.option('--account-index', default=None, type=int, help='Account index to use.')
@click.option('--track-messages', is_flag=True, default=True, help='Track message status after transfer.')
@click.option('--wait-status', is_flag=True, default=False, help='Wait until message is finalized on OffRamp.')
@click.option('--notify-email', default=None, help='Email to notify.')
@click.option('--estimate', default=None, type=int, help='Enter a fee estimate for your transfer, can leave as none.')
def transfer(to, dest, amount, source, batch_file, account_index, track_messages, wait_status, notify_email, estimate):
    """Send CCIP transfer (single or batch)."""
    if batch_file:
        logger.info(f"Running batch transfer from file: {batch_file}")
        batch_transfer(
            batch_file,
            source_network=source,
            account_index=account_index,
            track_messages=track_messages,
            wait_for_status=wait_status
        )
    else:
        if not all([to, dest, amount]):
            raise click.UsageError("Provide --to, --dest, and --amount for single transfer.")

        logger.info(f"Sending single transfer to {to} on {dest}")
        receipt, links, success, message_id = send_ccip_transfer(
            to_address=to,
            dest_chain=dest,
            amount=amount,
            source_chain=source,
            account_index=account_index,
            estimate=estimate
        )

        print(f"Source TX: {links['source_url']}")
        print(f"CCIP Explorer: {links['ccip_url']}")

        tx_hash = receipt.transactionHash.hex()
        logger.info(f"CCIP Transfer Submitted: {tx_hash}, Message ID: {message_id}")

        if success:
            if track_messages:
                status, address = check_ccip_message_status(
                    message_id_hex=message_id,
                    dest_chain=dest,
                    wait=wait_status
                )
                if status == "NOT_FOUND":
                    print(f"Message {message_id} not found.")
                else:
                    print(f"Status: {status} | OffRamp: {address}")
        else:
            print(f"Transaction was not successful (status=0). Try again with higher gas limit or fee parameters.")

        # === Notifications ===
        subject = "CCIP Transfer Submitted" if receipt.status == 1 else "CCIP Transfer Failed"
        body = (
            f"Your transfer to {dest} was successfully submitted.\n\nTx Hash: {tx_hash}"
            if receipt.status == 1
            else f"Transfer to {dest} failed or reverted on-chain.\n\nTx Hash: {tx_hash}\nPlease review gas settings or logs."
        )

        if notify_email:
            send_email_notification(subject, body, notify_email)

# Checking CCIP Status
@cli.command()
@click.option('--message-id', required=True, help='CCIP message ID (hex string with 0x).')
@click.option('--dest-chain', required=True, help='Destination chain name.')
@click.option('--wait', is_flag=True, help='Poll until message is found or timeout is reached.')
@click.option('--timeout', default=30*60, help='Max time (in seconds) to wait for message status if --wait is set.')
@click.option('--interval', default=120, help='Polling interval in seconds.')
def ccip_status(message_id, dest_chain, wait, timeout,interval,max_retries=120):
    """Check the status of a CCIP message."""
    from ccip_terminal.ccip import check_ccip_message_status

    max_retries = timeout // interval if wait else 1

    print(f"Checking CCIP status for {message_id} on {dest_chain}...")
    status, address = check_ccip_message_status(
        message_id_hex=message_id,
        dest_chain=dest_chain,
        wait=wait,
        poll_interval=interval,
        max_retries=max_retries
    )

    if status == "NOT_FOUND":
        print(f"Message {message_id} not found.")
    else:
        print(f"Status: {status} | OffRamp: {address}")

# ⏰ SCHEDULE TRANSFER
@cli.command()
@click.option('--to', required=True, help='Destination wallet.')
@click.option('--amount', required=True, type=float, help='Amount in USDC.')
@click.option('--dest', required=True, help='Destination chain.')
@click.option('--source', default="ethereum", help='Source chain.')
@click.option('--account-index', default=0, help='Account index to use.')
@click.option('--cron', required=True, help='Cron schedule (e.g. "0 9 * * *")')
def schedule_transfer(to, amount, dest, source, account_index, cron):
    """Schedule a CCIP transfer."""
    schedule_ccip_transfer(to, amount, dest, source, account_index, cron)
    start_scheduler_server()

@cli.command()
@click.option('--insecure-save', is_flag=True, help="Save private key to .env file (Not recommended).")
@click.option('--encrypt', is_flag=True, help="Encrypt private key and save to wallet_keystore.json.")
def create_wallet(insecure_save, encrypt):
    """Create a new Ethereum wallet."""
    private_key, address = generate_wallet()
    click.echo(f"Wallet Address: {address}")
    click.echo(f"Private Key: {private_key}")
    click.echo("IMPORTANT: Back up your private key safely.")

    if insecure_save:
        save_to_env(private_key)

    if encrypt:
        password = getpass("Enter password for keystore encryption: ")
        encrypt_keystore(private_key, password)

    click.echo("Wallet setup complete.")

# 📒 ADDRESS BOOK
@cli.group()
def address():
    """Manage your saved wallet addresses."""
    pass

@address.command()
@click.option('--name', required=True, help='Label for the wallet.')
@click.option('--address', required=True, help='Wallet address.')
def add(name, address):
    book = load_address_book()
    book[name] = address
    save_address_book(book)
    click.echo(f"Added {name} → {address}")

@address.command()
def list():
    book = load_address_book()
    if not book:
        click.echo("Address book is empty.")
    for name, addr in book.items():
        click.echo(f"{name}: {addr}")

@address.command()
@click.option('--name', required=True, help='Name to remove.')
def remove(name):
    book = load_address_book()
    if name in book:
        del book[name]
        save_address_book(book)
        click.echo(f"🗑 Removed {name}")
    else:
        click.echo("❌ Not found.")

# 🔑 (Optional) Fiat Onramps are For KYB'd Clients...

# # RAMP ONRAMP
# @cli.command()
# @click.option('--wallet', required=True, help='Wallet address')
# @click.option('--amount', default=100, help='Amount in fiat (e.g. 100 USD)')
# @click.option('--network', default='arbitrum', help='Crypto network (e.g. ethereum, arbitrum)')
# @click.option('--crypto', default='eth', help='Crypto token to buy (e.g. eth, usdc)')
# def ramp_onramp(wallet, amount, network, crypto):
#     """Generate a Ramp URL for fiat onramp."""
#     from fiat_ramps.ramp import create_ramp_url
#     url = create_ramp_url(wallet, amount, network, crypto)
#     import webbrowser
#     webbrowser.open(url)

# # 💸 TRANSAK ONRAMP
# @cli.command()
# @click.option('--wallet', required=True, help='User wallet address.')
# @click.option('--amount', required=True, type=float, help='Fiat amount in USD.')
# @click.option('--network', default="ethereum", help='Blockchain network.')
# @click.option('--with-webhook', is_flag=True, help='Start webhook server to listen for completion.')
# @click.option('--purchase-type', default="usdc", type=click.Choice(['usdc', 'gas']), help='Purchase type: USDC or gas token.')
# def transak_onramp(wallet, amount, network, with_webhook, purchase_type):
#     """Create Fiat → USDC (or gas token) payment session."""
#     if with_webhook:
#         run_webhook_server()

#     create_transak_session(wallet, amount, network, purchase_type)

if __name__ == "__main__":
    cli()
