import csv
import logging
import os
from pathlib import Path
import json
import time

from ccip_terminal.logger import logger
from ccip_terminal.ccip import send_ccip_transfer, check_ccip_message_status, get_ccip_fee_estimate
from ccip_terminal.account_state import get_usdc_data, prepare_transfer_data
from ccip_terminal.utils import calculate_usd_values

def track_ccip_messages(tracked_messages, wait_for_status=False, poll_interval=120, max_retries=30):

    attempts = 0
    pending = tracked_messages.copy()

    while pending and attempts < max_retries:
        next_round = []

        for tx in pending:
            message_id = tx["message_id"]
            dest_chain = tx["dest_chain"]
            print(f"Checking status for message: {message_id} on {dest_chain}")

            status, offramp = check_ccip_message_status(
                message_id_hex=message_id,
                dest_chain=dest_chain,
                wait=False  # Always non-blocking here
            )

            if status == "NOT_FOUND":
                print(f"Status pending for {message_id}")
                next_round.append(tx)
            else:
                logger.info(f"Message ID {message_id} | Status: {status} | OffRamp: {offramp}")

        if not wait_for_status or not next_round:
            break

        attempts += 1
        if next_round:
            print(f"Waiting {poll_interval} seconds before retry {attempts}/{max_retries}...")
            time.sleep(poll_interval)

        pending = next_round

def batch_transfer(batch_file, source_network=None, account_index=None, track_messages=False, wait_for_status=False):
    batch_file = Path(batch_file)
    if not batch_file.exists():
        logger.error(f"Batch file {batch_file} not found.")
        return

    # Load JSON or CSV
    try:
        if batch_file.suffix.lower() == ".json":
            with open(batch_file) as f:
                transfers = json.load(f)
        elif batch_file.suffix.lower() == ".csv":
            with open(batch_file) as f:
                reader = csv.DictReader(f)
                transfers = [row for row in reader]
        else:
            logger.error("Unsupported batch file format.")
            return
    except Exception as e:
        logger.error(f"Failed to load batch file: {e}")
        return

    tracked_messages = []

    for entry in transfers:
        to_address = str(entry.get("to_address"))
        amount = float(entry.get("amount", 0))
        dest = str(entry.get("dest"))

        if not all([to_address, dest, amount]):
            logger.warning(f"Skipping incomplete entry: {entry}")
            continue

        sender_found = False

        try:
            # Pre-estimate fees and filter accounts
            estimate = get_ccip_fee_estimate(to_address, dest, amount)
            min_estimate_eth = estimate['total_estimate'] / 1e18

            transfer_data = prepare_transfer_data(
                dest_chain=dest,
                source_chain=source_network,
                account_index=account_index,
                min_gas_threshold=min_estimate_eth
            )

            account_obj = transfer_data["account"]
            usable_source = transfer_data["source_chain"]
            usable_index = transfer_data["account_index"]

            # Send transfer
            receipt, links, success, message_id = send_ccip_transfer(
                to_address=to_address,
                dest_chain=dest,
                amount=amount,
                source_chain=usable_source,
                account_index=usable_index,
                estimate=estimate['total_estimate'] / 1e18  # reuse estimate for threshold match
            )

            if success:
                logger.info(f"Sent {amount} USDC to {to_address} | TX: {receipt.transactionHash.hex()} | ID: {message_id}")
                tracked_messages.append({"message_id": message_id, "dest_chain": dest})
                sender_found = True
            else:
                logger.warning(f"TX failed for {to_address} (check status manually)")
        except Exception as e:
            logger.error(f"Transfer failed for {to_address} | Error: {e}")

        if not sender_found:
            logger.warning(f"No sender found with sufficient balance/gas for {amount} USDC to {to_address}")

    if track_messages and tracked_messages:
        track_ccip_messages(
            tracked_messages=tracked_messages,
            wait_for_status=wait_for_status,
            poll_interval=120,
            max_retries=30
        )







