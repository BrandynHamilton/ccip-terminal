# ccip_terminal/scheduler/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from ccip_terminal.core import send_ccip_transfer
from ccip_terminal.logger import logger
from flask import Flask, jsonify

scheduler = BackgroundScheduler()
scheduled_jobs = []

def schedule_ccip_transfer(wallet, amount, dest_chain, source_chain, account_index, cron_expr):
    """
    Schedule a CCIP transfer.
    """
    def job():
        print(f"🚀 Scheduled CCIP transfer: {amount} USDC → {dest_chain} → {wallet}")
        receipt, links, success, message_id = send_ccip_transfer(to_address=wallet, dest_chain=dest_chain, amount=amount, 
                                    source_chain=source_chain, account_index=account_index)
        if success:
            logger.info(f"CCIP Transfer Submitted Successfully: {receipt.transactionHash.hex()}, Message ID: {message_id}")
        else:
            logger.info(f"CCIP Transfer Failed: {receipt.transactionHash.hex()}, Message ID: {message_id}")
            
        print(f"Source TX: {links['source_url']}")
        print(f"CCIP Explorer: {links['ccip_url']}")

    trigger = CronTrigger.from_crontab(cron_expr)
    job_ref = scheduler.add_job(job, trigger)
    scheduled_jobs.append({
        "wallet": wallet,
        "amount": amount,
        "dest_chain": dest_chain,
        "source_chain": source_chain,
        "cron": cron_expr,
        "job_id": job_ref.id
    })
    print(f"📅 Transfer scheduled: {wallet}, {amount}, {dest_chain}, cron: {cron_expr}")

def start_scheduler_server():
    """
    Start Flask server + scheduler to manage CCIP transfers.
    """
    app = Flask(__name__)

    @app.route("/scheduled", methods=["GET"])
    def list_jobs():
        return jsonify(scheduled_jobs)

    scheduler.start()
    app.run(port=5002)
