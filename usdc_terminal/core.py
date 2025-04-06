import csv
import logging
import os
from pathlib import Path
import json

from usdc_terminal.logger import logger
from usdc_terminal.token_utils import get_balance
from usdc_terminal.accounts import load_accounts
from usdc_terminal.network import network_func
from usdc_terminal.ccip import send_ccip_transfer, get_ccip_fee_api, check_ccip_message_status
from usdc_terminal.notifications import send_email_notification, send_sms_notification

def batch_transfer(batch_file, source_network='arbitrum', account_index=0):

    batch_file = Path(batch_file)
    if not batch_file.exists():
        logger.error(f"Batch file {batch_file} not found.")
        return

    transfers = []

    # Detect file type and load
    if batch_file.suffix.lower() == '.json':
        try:
            with open(batch_file, 'r') as f:
                transfers = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return
    elif batch_file.suffix.lower() == '.csv':
        try:
            with open(batch_file, 'r') as f:
                reader = csv.DictReader(f)
                transfers = [row for row in reader]
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return
    else:
        logger.error(f"Unsupported file format: {batch_file.suffix}")
        return

    # Iterate and process transfers
    for entry in transfers:
        to_address = str(entry.get('to_address'))
        amount = float(entry.get('amount', 0))
        dest = str(entry.get('dest'))
        memo = str(entry.get('memo', ""))

        if not all([to_address, dest, amount]):
            logger.warning(f"Skipping incomplete transfer: {entry}")
            continue

        try:
            receipt, message_id = send_ccip_transfer(to_address=to_address, dest_chain=dest, amount=amount, 
                                    source_chain=source_network, account_index=account_index)
            logger.info(f"Transfer to {to_address} of {amount} USDC successful. TX: {receipt.TransactionHash.hash()}, messageId: {message_id}")
        except Exception as e:
            logger.error(f"Transfer to {to_address} failed. Error: {e}")



