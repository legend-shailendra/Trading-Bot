"""
client.py
---------
Initialises and exposes the authenticated Binance Futures Testnet client.

The `python-binance` library supports the Futures Testnet via dedicated
constructor flags.  We expose a single ``get_client()`` factory so every
other module obtains the same configured instance without touching raw
credentials.

Environment variables expected:
    BINANCE_API_KEY   – Your Binance Futures Testnet API key
    BINANCE_SECRET_KEY – Your Binance Futures Testnet secret key
"""

from __future__ import annotations

import os
from pathlib import Path

from binance.client import Client
from binance.exceptions import BinanceAPIException

from bot.logging_config import logger

# Binance Futures Testnet base URLs
_FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"

# The .env file lives at  trading_bot/.env  (two levels up from this file)
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

_client_instance: Client | None = None


def _load_env_file() -> None:
    """
    Read trading_bot/.env and inject keys into os.environ.

    Works with or without the python-dotenv package installed.
    Runs every time get_client() is called on a fresh (un-cached) instance
    so the Flask process always picks up the correct credentials.
    """
    # ── Try python-dotenv first ──────────────────────────────────────────
    try:
        from dotenv import load_dotenv
        if _ENV_FILE.exists():
            load_dotenv(_ENV_FILE, override=True)
            logger.debug("Credentials loaded via python-dotenv from %s", _ENV_FILE)
            return
    except ImportError:
        pass

    # ── Pure-Python fallback: parse the .env file manually ──────────────
    if not _ENV_FILE.exists():
        return
    try:
        with open(_ENV_FILE, encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key:
                    os.environ[key] = val
        logger.debug("Credentials loaded via built-in parser from %s", _ENV_FILE)
    except OSError as exc:
        logger.warning("Could not read .env file: %s", exc)


def get_client() -> Client:
    """
    Return a singleton Binance ``Client`` configured for the Futures Testnet.

    Credentials are read from (in priority order):
      1. trading_bot/.env  (loaded fresh on every first-call attempt)
      2. Process environment variables set before Python started

    Returns:
        Authenticated ``binance.client.Client`` instance.

    Raises:
        EnvironmentError: If credentials are missing after all attempts.
        BinanceAPIException: If the Binance API rejects the credentials.
    """
    global _client_instance

    if _client_instance is not None:
        return _client_instance

    # Always load .env so this works even when started via `python app.py`
    # with no shell env vars pre-set.
    _load_env_file()

    api_key    = os.environ.get("BINANCE_API_KEY",    "").strip()
    api_secret = os.environ.get("BINANCE_SECRET_KEY", "").strip()

    if not api_key or not api_secret:
        msg = (
            "BINANCE_API_KEY and BINANCE_SECRET_KEY are not set.\n"
            "Add them to trading_bot/.env:\n"
            "  BINANCE_API_KEY=your_key_here\n"
            "  BINANCE_SECRET_KEY=your_secret_here\n"
            f"  (.env expected at: {_ENV_FILE})"
        )
        logger.critical(msg)
        raise EnvironmentError(msg)

    logger.info(
        "Initialising Binance Futures Testnet client (key ends ...%s).", api_key[-6:]
    )

    try:
        client = Client(
            api_key=api_key,
            api_secret=api_secret,
            testnet=True,
        )

        # Override base URLs to guarantee futures endpoints hit the testnet
        client.FUTURES_URL      = f"{_FUTURES_TESTNET_BASE_URL}/fapi"
        client.FUTURES_DATA_URL = f"{_FUTURES_TESTNET_BASE_URL}/futures/data"
        client.FUTURES_COIN_URL = f"{_FUTURES_TESTNET_BASE_URL}/dapi"

        # Connectivity + auth check
        server_time = client.get_server_time()
        logger.info("Connected to Futures Testnet. Server time: %s", server_time)

        _client_instance = client
        return _client_instance

    except BinanceAPIException as exc:
        logger.error("Binance API error during client init: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error during client init: %s", exc)
        raise


def reset_client() -> None:
    """Force the next ``get_client()`` call to create a fresh instance."""
    global _client_instance
    _client_instance = None
    logger.debug("Client instance reset.")
