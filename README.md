# Primetrade Trading Bot — Binance Futures Testnet

> A production-ready Python bot that places **Market** and **Limit** orders on the [Binance Futures Testnet](https://testnet.binancefuture.com).  
> Comes with a fully-featured **CLI** and a polished **web UI** built with Flask.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package marker
│   ├── client.py            # Singleton Binance Testnet client
│   ├── orders.py            # Order logic + OrderResult dataclass
│   ├── validators.py        # Input validation (no API calls)
│   ├── logging_config.py    # Rotating log file + console logger
│   └── cli.py               # argparse CLI entry point
├── app.py                   # Flask web UI
├── requirements.txt
└── README.md
```

---

## 1 — Prerequisites

| Requirement | Version |
|---|---|
| Python | ≥ 3.10 |
| pip | latest |

---

## 2 — Installation

```bash
# Clone / navigate into the project root
cd trading_bot

# Create and activate a virtual environment (recommended)
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 3 — Obtain Testnet API Credentials

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com).
2. Log in with your GitHub account (no KYC needed).
3. Go to **API Management** and create a new key pair.
4. Copy the **API Key** and **Secret Key** — you will only see the secret once.

> ⚠️ These credentials only work on the Testnet. Never use real Binance keys here.

---

## 4 — Set Environment Variables

The bot reads credentials exclusively from environment variables.

### Windows (PowerShell)

```powershell
$env:BINANCE_API_KEY   = "your_testnet_api_key_here"
$env:BINANCE_SECRET_KEY = "your_testnet_secret_key_here"
```

### macOS / Linux (bash / zsh)

```bash
export BINANCE_API_KEY="your_testnet_api_key_here"
export BINANCE_SECRET_KEY="your_testnet_secret_key_here"
```

> 💡 Add these lines to your shell profile (`.bashrc`, `.zshrc`, or a `.env` file loaded by `direnv`) to avoid re-entering them each session.

---

## 5 — CLI Usage

Run from the **`trading_bot/`** directory (where `bot/` lives).

### Syntax

```bash
python -m bot.cli place <SYMBOL> <SIDE> <ORDER_TYPE> <QUANTITY> [--price PRICE]
```

### Examples

```bash
# ── Market Orders ───────────────────────────────────────────────────

# Buy 0.001 BTC at market price
python -m bot.cli place BTCUSDT BUY MARKET 0.001

# Sell 0.01 ETH at market price
python -m bot.cli place ETHUSDT SELL MARKET 0.01

# ── Limit Orders ────────────────────────────────────────────────────

# Buy 0.001 BTC when price drops to $62,000
python -m bot.cli place BTCUSDT BUY LIMIT 0.001 --price 62000

# Sell 0.01 ETH when price reaches $3,500
python -m bot.cli place ETHUSDT SELL LIMIT 0.01 --price 3500

# ── Help ────────────────────────────────────────────────────────────
python -m bot.cli --help
python -m bot.cli place --help
```

### Sample Output (success)

```
==========================================
  📋  ORDER REQUEST SUMMARY
==========================================
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
  Price      : N/A (MARKET)
==========================================

╔══════════════════════════════════════╗
║         ORDER PLACED SUCCESSFULLY    ║
╚══════════════════════════════════════╝
  Order ID       : 3728954012
  Client OID     : web_abc123
  Symbol         : BTCUSDT
  Side           : BUY
  Type           : MARKET
  Status         : FILLED
  Quantity       : 0.001
  Executed Qty   : 0.001
  Avg Price      : 64823.10
  Time In Force  : GTC

✅  Order placed successfully!
```

---

## 6 — Web UI Usage

```bash
# From the trading_bot/ directory:
python app.py
```

Open **[http://localhost:5000](http://localhost:5000)** in your browser.

### Optional environment variables for the web server

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Port to listen on |
| `FLASK_DEBUG` | `false` | Set to `true` for auto-reload in development |

```powershell
# Example: run on port 8080 with debug mode
$env:PORT = "8080"
$env:FLASK_DEBUG = "true"
python app.py
```

### UI Features
- **BUY / SELL chips** — visual toggle with colour feedback (green / red).
- **Dynamic price field** — appears only when *Limit* is selected.
- **Order result panel** — renders `orderId`, `status`, `executedQty`, and `avgPrice` after every submission.
- **Health endpoint** — `GET /health` returns `{"status": "ok"}` for uptime monitoring.

---

## 7 — Logging

All activity is written to **`trading_bot.log`** in the project root and echoed to the console.

```
2024-05-08 14:32:01 | INFO     | trading_bot | Logging initialised. Log file: trading_bot.log
2024-05-08 14:32:01 | INFO     | trading_bot | Initialising Binance Futures Testnet client (key ends …3XkR).
2024-05-08 14:32:02 | INFO     | trading_bot | Connected to Futures Testnet. Server time: {'serverTime': 1715176322000}
2024-05-08 14:32:02 | INFO     | trading_bot | Placing BUY MARKET order | symbol=BTCUSDT | qty=0.001 | price=None
2024-05-08 14:32:02 | INFO     | trading_bot | Order placed successfully: orderId=3728954012, status=FILLED
```

The log file rotates automatically at **5 MB** with **3 backups** kept.

---

## 8 — Error Handling

| Error Class | Behaviour |
|---|---|
| Missing env variables | `EnvironmentError` with setup instructions; graceful CLI message |
| Invalid inputs | `ValueError` from validators; printed without traceback |
| Binance API rejection | `BinanceAPIException`; error code + message shown |
| Network / timeout | Generic `Exception`; full traceback in log, clean message in UI |

---

## 9 — Architecture Overview

```
CLI (bot/cli.py)          Web UI (app.py)
       │                        │
       └───────────┬────────────┘
                   ▼
         bot/validators.py   ← pure validation, no I/O
                   │
                   ▼
           bot/orders.py     ← places order, returns OrderResult
                   │
                   ▼
           bot/client.py     ← singleton Binance Testnet client
                   │
                   ▼
      Binance Futures Testnet API
      https://testnet.binancefuture.com
```

---

## 10 — Running Tests (optional)

```bash
pip install pytest

# Set dummy credentials so the client module doesn't raise
$env:BINANCE_API_KEY    = "test_key"
$env:BINANCE_SECRET_KEY = "test_secret"

pytest -v
```

---

## License

MIT — free to use, modify, and distribute.
