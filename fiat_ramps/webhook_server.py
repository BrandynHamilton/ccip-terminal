# fiat_ramps/webhook_server.py

from flask import Flask, request
import threading
from usdc_transfer.core import send_ccip_transfer
from .config import WEBHOOK_PORT

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.json
    event = payload.get("event")
    data = payload.get("data", {})

    if event == "TRANSACTION_COMPLETED":
        wallet = data.get("walletAddress")
        amount = data.get("cryptoAmount")
        network = data.get("network")

        print(f"✅ Fiat payment completed for {wallet}: {amount} USDC on {network}")

        # You can trigger CCIP transfer here
        # Example:
        # send_ccip_transfer(wallet, "destination_chain", float(amount), "source_chain")

    return "ok", 200

def run_webhook_server():
    """
    Run the webhook server.
    """
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=WEBHOOK_PORT)).start()
    print(f"🌐 Webhook server running on port {WEBHOOK_PORT}")
