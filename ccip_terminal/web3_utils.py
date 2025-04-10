from ccip_terminal.utils import load_abi, get_dynamic_gas_fees
from ccip_terminal.logger import logger
from ccip_terminal.utils import generate_explorer_links
from web3 import Web3

def send_same_chain_transfer(w3, token_address, sender_account, to_address, amount, decimals):
    
    erc20_abi = load_abi()["erc20_abi"]
    token = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc20_abi)

    amount_wei = int(amount * (10 ** decimals))
    token_balance = token.functions.balanceOf(Web3.to_checksum_address(sender_account.address)).call()
    
    if token_balance < amount_wei:
        raise Exception(f"Insufficient token balance. Have: {token_balance}, Need: {amount_wei}")
    nonce = w3.eth.get_transaction_count(sender_account.address)
    fees = get_dynamic_gas_fees(w3)

    # Build the tx object (without gas)
    tx = token.functions.transfer(
        Web3.to_checksum_address(to_address),
        amount_wei
    ).build_transaction({
        'from': sender_account.address,
        'nonce': nonce,
        'chainId': w3.eth.chain_id,
    })

    # Dynamically estimate gas
    gas_limit = w3.eth.estimate_gas(tx)

    # Add EIP-1559 fields
    tx.update({
        'gas': int(gas_limit*1.15),
        'maxFeePerGas': fees['max_fee_per_gas'],
        'maxPriorityFeePerGas': fees['max_priority_fee'],
        'type': 2,
    })

    signed_tx = sender_account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return w3.eth.wait_for_transaction_receipt(tx_hash)

def try_send_tx(source_chain, router, dest_selector, message, tx_params, w3, account):
    try:
        # Optional pre-fetch of messageId
        try:
            message_id = router.functions.ccipSend(dest_selector, message).call({
                "from": account.address,
                "value": tx_params["value"]
            })
            logger.info(f"CCIP messageId (pre-send): {message_id.hex()}")
        except Exception as pre_e:
            logger.warning(f"Could not prefetch messageId: {pre_e}")
            message_id = None

        tx = router.functions.ccipSend(dest_selector, message).build_transaction(tx_params)
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        links = generate_explorer_links(source_chain, tx_hash, message_id.hex() if message_id else None)
        success = receipt.status == 1

        if not success:
            logger.warning(f"TX {tx_hash.hex()} mined but failed. Check: {links['source_url']}")
            try:
                failed_tx = w3.eth.get_transaction(tx_hash)
                w3.eth.call(failed_tx, block_identifier=receipt.blockNumber)
            except Exception as revert_e:
                logger.warning(f"Revert reason: {revert_e}")
                logger.error(f"TX Failed inside try_send_tx. TX Hash: {tx_hash.hex()} | Links: {links}")
                raise Exception("TX failed with status=0")  # Clean exception to trigger retry

        return receipt, links, success, '0x' + message_id.hex() if message_id else None

    except Exception as e:
        logger.error(f"TX Failed inside try_send_tx: {e}")
        raise e  # Re-raise with full context

