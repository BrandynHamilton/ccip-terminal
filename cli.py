import os
import json
import click

from usdc_transfer.core import batch_transfer
from usdc_transfer.ccip import send_ccip_transfer
from usdc_transfer.notifications import send_email_notification, send_sms_notification
from usdc_transfer.logger import logger
from fiat_ramps import create_transak_session, run_webhook_server
from scheduler import schedule_ccip_transfer, start_scheduler_server

import sys
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

ADDRESS_BOOK_FILE = "address_book.json"

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

# 🚀 TRANSFER COMMAND
@cli.command()
@click.option('--to', help='Destination wallet address.')
@click.option('--dest', help='Destination chain.')
@click.option('--amount', type=float, help='Amount to send.')
@click.option('--source', default='arbitrum', help='Source chain.')
@click.option('--batch-file', type=click.Path(), help='Path to batch JSON or CSV file.')
@click.option('--account-index', default=0, help='Account index to use.')
@click.option('--notify-email', default=None, help='Email to notify.')
@click.option('--notify-sms', default=None, help='Phone number to notify.')
def transfer(to, dest, amount, source, batch_file, account_index, notify_email, notify_sms):
    """Send CCIP transfer (single or batch)."""
    tx_hash = None

    if batch_file:
        logger.info(f"Running batch transfer from file: {batch_file}")
        batch_transfer(batch_file, account_index)
    else:
        if not all([to, dest, amount]):
            raise click.UsageError("Provide --to, --dest, and --amount for single transfer.")

        logger.info(f"Sending single transfer to {to} on {dest}")
        receipt, message_id = send_ccip_transfer(to_address=to, dest_chain=dest, amount=amount, 
                                    source_chain=source, account_index=account_index)
        logger.info(f"CCIP Transfer Submitted: {receipt.transactionHash.hex()}, Message ID: {message_id}")

        if notify_email:
            send_email_notification("CCIP Transfer Complete", f"Your transfer to {dest} was submitted. Tx: {tx_hash}", notify_email)
        if notify_sms:
            send_sms_notification(f"CCIP Transfer submitted to {dest}. Tx: {tx_hash}", notify_sms)

# Checking CCIP Status
@cli.command()
@click.option('--message-id', required=True, help='CCIP message ID (hex string with 0x).')
@click.option('--dest-chain', required=True, help='Destination chain name.')
@click.option('--wait', is_flag=True, help='Poll until message is found or timeout is reached.')
@click.option('--timeout', default=30*60, help='Max time (in seconds) to wait for message status if --wait is set.')
@click.option('--interval', default=120, help='Polling interval in seconds.')
def ccip_status(message_id, dest_chain, wait, timeout, max_retries):
    """Check the status of a CCIP message."""
    from usdc_transfer.monitoring import check_ccip_message_status

    max_retries = timeout // interval if wait else 1

    print(f"🔎 Checking CCIP status for {message_id} on {dest_chain}...")
    status, address = check_ccip_message_status(
        message_id_hex=message_id,
        dest_chain=dest_chain,
        wait=wait,
        poll_interval=interval,
        max_retries=max_retries
    )

    if status == "NOT_FOUND":
        print(f"❌ Message {message_id} not found.")
    else:
        print(f"✅ Status: {status} | OffRamp: {address}")

# 💸 FIAT ONRAMP
@cli.command()
@click.option('--wallet', required=True, help='User wallet address.')
@click.option('--amount', required=True, type=float, help='Fiat amount in USD.')
@click.option('--network', default="ethereum", help='Blockchain network.')
@click.option('--with-webhook', is_flag=True, help='Start webhook server to listen for completion.')
@click.option('--purchase-type', default="usdc", type=click.Choice(['usdc', 'gas']), help='Purchase type: USDC or gas token.')
def fiat_onramp(wallet, amount, network, with_webhook, purchase_type):
    """Create Fiat → USDC (or gas token) payment session."""
    if with_webhook:
        run_webhook_server()

    create_transak_session(wallet, amount, network, purchase_type)

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
    click.echo(f"✅ Added {name} → {address}")

@address.command()
def list():
    book = load_address_book()
    if not book:
        click.echo("📭 Address book is empty.")
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

# 🔑 (Optional) WALLET GEN COMING LATER...

if __name__ == "__main__":
    cli()
