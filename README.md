# `ccip-terminal` Documentation

**ccip-terminal** is a Python package and CLI for managing cross-chain token transfers using Chainlink CCIP.

The package can be considered a self-custodial bridge; it supports batch transfers, scheduled jobs, CCIP status monitoring, and address book utilities.

For now the package **only supports USDC**; other currencies will be added later.  

This package supports testnet CCIP as well.

## Installation

```bash
# Install via uv
pip install uv  # Only if not already installed
uv pip install ccip_terminal[all] # For both core and scheduler packages

# By name
uv pip install ccip-terminal # Base library
uv pip install ccip-terminal[scheduler]
uv pip install ccip-terminal[all] #Both base and scheduler 

```

## CLI Usage

```bash
uv run python cli.py [COMMAND] [OPTIONS]
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
| `--wait-status`   | (optional) Wait for CCIP Tx to Finalize     |
| `--notify-email`  | (optional) Email address to notify          |
| `--estimate`      | (optional) A Fee Estimate Value             |

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
ccip_terminal/
├── cli.py
├── ccip_terminal/
│   ├── core.py
│   ├── ccip.py
│   ├── logger.py
│   ├── accounts.py
│   ├── env.py
│   └── ...
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
ETHERSCAN_API_KEY =
SMTP_SERVER=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
NETWORK_TYPE=
```

## INFURA_API_KEY is the only required variable, but ETHERSCAN_API_KEY is also reccomended for accurate gas estimation.
## NETWORK_TYPE environment variable expects either "testnet" or "mainnet", and defaults to "mainnet"

## License

MIT License

## Contact Info

- [brandynhamilton@gmail.com](mailto:brandynhamilton@gmail.com)