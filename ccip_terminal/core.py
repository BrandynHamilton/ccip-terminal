import csv
import logging
import os
from pathlib import Path
import json
import time

from ccip_terminal.logger import logger
from ccip_terminal.token_utils import get_balance
from ccip_terminal.accounts import load_accounts
from ccip_terminal.network import network_func
from ccip_terminal.ccip import send_ccip_transfer, get_ccip_fee_api, check_ccip_message_status
from ccip_terminal.notifications import send_email_notification, send_sms_notification
from ccip_terminal.account_state import get_usdc_data
from ccip_terminal.utils import calculate_usd_values


def track_ccip_messages(tracked_messages, wait_for_status=False, poll_interval=120, max_retries=15):
    from ccip_terminal.ccip import check_ccip_message_status

    attempts = 0
    pending = tracked_messages.copy()

    while pending and attempts < max_retries:
        next_round = []

        for tx in pending:
            message_id = tx["message_id"]
            dest_chain = tx["dest_chain"]
            print(f"🔍 Checking status for message: {message_id} on {dest_chain}")

            status, offramp = check_ccip_message_status(
                message_id_hex=message_id,
                dest_chain=dest_chain,
                wait=False  # Always non-blocking here
            )

            if status == "NOT_FOUND":
                print(f"⏳ Status pending for {message_id}")
                next_round.append(tx)
            else:
                logger.info(f"✅ Message ID {message_id} | Status: {status} | OffRamp: {offramp}")

        if not wait_for_status or not next_round:
            break

        attempts += 1
        if next_round:
            print(f"⏲️ Waiting {poll_interval} seconds before retry {attempts}/{max_retries}...")
            time.sleep(poll_interval)

        pending = next_round

def batch_transfer(batch_file, source_network=None, account_index=None, min_gas_threshold=0.001, track_messages=False, wait_for_status=False):

    batch_file = Path(batch_file)
    if not batch_file.exists():
        logger.error(f"Batch file {batch_file} not found.")
        return

    # Load transfers
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

    # Preload balances
    BALANCES_DICT_RAW, TOKEN_CONTRACTS, TOKEN_DECIMALS, account_obj, usdc_price = get_usdc_data(account_index=None)
    BALANCES_DICT = calculate_usd_values(BALANCES_DICT_RAW, usdc_price)

    # Flatten all balances (for dynamic mode)
    def refresh_balances():
        flat = []
        for wallet_index, (wallet, data) in enumerate(BALANCES_DICT_RAW.items()):
            for network, balance_data in data.items():
                if isinstance(balance_data, dict) and balance_data.get("native_token", 0) >= min_gas_threshold:
                    flat.append({
                        "wallet": wallet,
                        "network": network,
                        "usdc": balance_data.get("usdc", 0),
                        "index": wallet_index
                    })
        return sorted(flat, key=lambda x: x["usdc"], reverse=True)

    sorted_balances = refresh_balances()
    tracked_messages = []

    for entry in transfers:
        to_address = str(entry.get("to_address"))
        amount = float(entry.get("amount", 0))
        dest = str(entry.get("dest"))

        if not all([to_address, dest, amount]):
            logger.warning(f"Skipping incomplete entry: {entry}")
            continue

        sender_found = False

        # Fixed account mode
        if source_network and account_index is not None:
            try:
                receipt, message_id = send_ccip_transfer(
                    to_address=to_address,
                    dest_chain=dest,
                    amount=amount,
                    source_chain=source_network,
                    account_index=account_index
                )
                logger.info(f"[Fixed] Sent {amount} USDC to {to_address} | TX: {receipt.transactionHash.hex()} | ID: {message_id}")
                tracked_messages.append({"message_id": message_id, "dest_chain": dest})
                sender_found = True
            except Exception as e:
                logger.error(f"[Fixed] Transfer failed for {to_address} | Error: {e}")
        else:
            # Dynamic account selection
            for candidate in sorted_balances:
                if candidate["usdc"] >= amount and candidate["network"] != dest:
                    try:
                        receipt, message_id = send_ccip_transfer(
                            to_address=to_address,
                            dest_chain=dest,
                            amount=amount,
                            source_chain=candidate["network"],
                            account_index=candidate["index"]
                        )
                        logger.info(f"[Dynamic] Sent {amount} USDC to {to_address} | TX: {receipt.transactionHash.hex()} | ID: {message_id}")
                        tracked_messages.append({"message_id": message_id, "dest_chain": dest})
                        sender_found = True

                        # Refresh balances after successful transfer
                        BALANCES_DICT_RAW, _, _, _, _ = get_usdc_data(account_index=None)
                        sorted_balances = refresh_balances()

                        break
                    except Exception as e:
                        logger.error(f"[Dynamic] Failed using {candidate['wallet']} on {candidate['network']} | Error: {e}")

        if not sender_found:
            logger.warning(f"No valid sender found for {amount} USDC to {to_address}")

    # Optionally track messages
    if track_messages and tracked_messages:
        track_ccip_messages(
            tracked_messages=tracked_messages,
            wait_for_status=wait_for_status,
            poll_interval=120,
            max_retries=30
        )







