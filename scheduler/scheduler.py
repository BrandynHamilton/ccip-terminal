# usdc_transfer/scheduler/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from usdc_transfer.core import send_ccip_transfer
from flask import Flask, jsonify

scheduler = BackgroundScheduler()
scheduled_jobs = []

def schedule_ccip_transfer(wallet, amount, dest_chain, source_chain, account_index, cron_expr):
    """
    Schedule a CCIP transfer.
    """
    def job():
        print(f"🚀 Scheduled CCIP transfer: {amount} USDC → {dest_chain} → {wallet}")
        tx_hash = send_ccip_transfer(wallet, dest_chain, amount, source_chain, account_index)
        print(f"✅ Transfer submitted: {tx_hash}")

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
