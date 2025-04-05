# 🔁 `usdc-transfer` CLI Documentation

**usdc-transfer** is a Python package and CLI for managing cross-chain USDC transfers using Chainlink CCIP.  
It supports batch transfers, fiat onramps, scheduled jobs, CCIP status monitoring, and address book utilities.

---

## 🛠️ Installation

```bash
pip install usdc-transfer
Make sure your .env file contains:

env
Copy
Edit
ETHERSCAN_API_KEY=your_etherscan_key
ALCHEMY_API_KEY=your_alchemy_key
INFURA_API_KEY=your_infura_key
TRANSAK_API_KEY=your_transak_key
🚀 Transfer Command
Send USDC using Chainlink CCIP.

➤ Single Transfer
bash
Copy
Edit
python cli.py transfer --to 0xRecipient... --dest optimism --amount 10
➤ Use Non-Ethereum Source Chain
bash
Copy
Edit
python cli.py transfer --to 0xRecipient... --dest base --source arbitrum --amount 5
➤ Batch Transfer
Use a JSON or CSV file with multiple transfer entries.

bash
Copy
Edit
python cli.py transfer --batch-file batch.json
➤ Send With Notifications
bash
Copy
Edit
python cli.py transfer \
  --to 0xRecipient... \
  --dest optimism \
  --amount 20 \
  --notify-email you@example.com \
  --notify-sms +1234567890
🧠 Check CCIP Status
Poll the destination chain for the status of a message.

bash
Copy
Edit
python cli.py ccip-status --message-id 0xYourMsgID... --dest-chain optimism
➤ Poll Until Success
bash
Copy
Edit
python cli.py ccip-status \
  --message-id 0xYourMsgID... \
  --dest-chain optimism \
  --wait --interval 15 --timeout 600
💵 Fiat Onramp (Transak Integration)
Creates a fiat onramp session via Transak.

bash
Copy
Edit
python cli.py fiat-onramp --wallet 0xYourWallet... --amount 100
➤ Onramp Gas Instead of USDC
bash
Copy
Edit
python cli.py fiat-onramp \
  --wallet 0xYourWallet... \
  --amount 20 \
  --purchase-type gas
➤ Start Webhook Server for Completion
bash
Copy
Edit
python cli.py fiat-onramp \
  --wallet 0xYourWallet... \
  --amount 50 \
  --with-webhook
⏰ Schedule Transfers
Run future or recurring transfers using cron syntax.

bash
Copy
Edit
python cli.py schedule-transfer \
  --to 0xRecipient... \
  --amount 5 \
  --dest base \
  --cron "0 9 * * *"
📒 Address Book Commands
➤ Add Address
bash
Copy
Edit
python cli.py address add --name Alice --address 0xAliceWallet...
➤ List Addresses
bash
Copy
Edit
python cli.py address list
➤ Remove Address
bash
Copy
Edit
python cli.py address remove --name Alice
🔧 Developer Notes
Modular CLI powered by Click

All transfers use EIP-1559 dynamic gas fees

Chain and address validation is done before execution

Works well with automated bots and cloud deployment

🧪 Coming Soon
🧬 Wallet generation and key encryption

📊 Transfer analytics and performance stats

🧠 LLM-enhanced transfer suggestions

Created with ❤️ by Optimizer Research

vbnet
Copy
Edit

Let me know if you want a CLI auto-generated help message (`--help` examples)
```
