# `usdc-transfer` Documentation

**usdc-transfer** is a Python package and CLI for managing cross-chain USDC transfers using Chainlink CCIP.  
It can be thought as a self-custodial bridge; it supports batch transfers, fiat onramps, scheduled jobs, CCIP status monitoring, and address book utilities.

## Installation

```bash
pip install -e .[all]

pip install usdc-transfer
pip install usdc-transfer[fiat-ramps]
pip install usdc-transfer[scheduler]
pip install usdc-transfer[all]

```

## CLI Usage

```bash
python cli.py [COMMAND] [OPTIONS]
```

## Commands

### transfer

Send a USDC transfer via Chainlink CCIP.

#### Options

| Option            | Description                                 |
| ----------------- | ------------------------------------------- |
| `--to`            | Destination wallet address                  |
| `--dest`          | Destination chain                           |
| `--amount`        | Amount to send                              |
| `--source`        | (optional) Source chain (default: ethereum) |
| `--batch-file`    | (optional) Path to batch JSON or CSV file   |
| `--account-index` | (optional) Account index to use             |
| `--notify-email`  | (optional) Email address to notify          |
| `--notify-sms`    | (optional) SMS number to notify             |

#### Examples

Single Transfer:

```bash
python cli.py transfer --to 0xabc... --dest arbitrum --amount 10
```

Batch Transfer:

```bash
python cli.py transfer --batch-file ./transfers/batch.json
```

---

### ccip-status

Check the status of a CCIP message.

#### Options

| Option         | Description                            |
| -------------- | -------------------------------------- |
| `--message-id` | CCIP message ID (with 0x)              |
| `--dest-chain` | Destination chain                      |
| `--wait`       | (optional) Wait for confirmation       |
| `--timeout`    | (optional) Max wait time in seconds    |
| `--interval`   | (optional) Polling interval in seconds |

#### Example

```bash
python cli.py ccip-status --message-id 0xabc... --dest-chain optimism
```

---

### fiat-onramp

Create a Transak fiat-onramp session.

#### Options

| Option            | Description                     |
| ----------------- | ------------------------------- |
| `--wallet`        | Wallet address to receive funds |
| `--amount`        | Fiat amount in USD              |
| `--network`       | (optional) Target network       |
| `--purchase-type` | USDC or gas token               |
| `--with-webhook`  | (optional) Run webhook listener |

#### Example

```bash
python cli.py fiat-onramp --wallet 0xabc... --amount 100
```

---

### schedule-transfer

Schedule a recurring transfer using cron.

#### Options

| Option            | Description                |
| ----------------- | -------------------------- |
| `--to`            | Destination wallet address |
| `--amount`        | Amount to send             |
| `--dest`          | Destination chain          |
| `--source`        | (optional) Source chain    |
| `--account-index` | (optional) Account index   |
| `--cron`          | Cron expression            |

#### Example

```bash
python cli.py schedule-transfer --to 0xabc... --amount 5 --dest optimism --cron "0 9 * * *"
```

---

### address

Manage a local address book.

#### Subcommands

- `add` → Save a new address
- `list` → View saved addresses
- `remove` → Delete an address by name

#### Examples

```bash
python cli.py address add --name Alice --address 0xabc...
python cli.py address list
python cli.py address remove --name Alice
```

---

## Project Structure

```
usdc-transfer/
├── cli.py
├── usdc_transfer/
│   ├── core.py
│   ├── ccip.py
│   ├── logger.py
│   ├── accounts.py
│   ├── env.py
│   └── ...
├── fiat_ramps/
│   ├── transak.py
│   └── webhook_server.py
├── scheduler/
│   └── ...
├── address_book.json
├── README.md
```

---

## Environment Variables

Create a `.env` file and include:

```
PRIVATE_KEYS=
COINGECKO_API_KEY =
ALCHEMY_API_KEY =
INFURA_API_KEY =
NOTIFY_EMAIL =
NOTIFY_PHONE =
ETHERSCAN_API_KEY =
SMTP_SERVER=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
```

## INFURA_API_KEY is the only required variable.

## License

MIT License
