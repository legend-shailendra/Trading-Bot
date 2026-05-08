"""
orders.py
---------
Order formatting, execution, and result presentation.

All order placements go through ``place_order()``.  The raw Binance
response is parsed and a clean ``OrderResult`` dataclass is returned so
upstream callers (CLI, web UI) can render it uniformly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from binance.exceptions import BinanceAPIException, BinanceOrderException

from bot.client import get_client
from bot.logging_config import logger


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class OrderResult:
    """Parsed response from a Binance order placement call."""

    success: bool
    order_id: Optional[int] = None
    client_order_id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    executed_qty: Optional[str] = None
    avg_price: Optional[str] = None
    orig_qty: Optional[str] = None
    time_in_force: Optional[str] = None
    raw_response: Optional[dict] = None
    error_message: Optional[str] = None

    def summary(self) -> str:
        """Return a human-readable summary string."""
        if self.success:
            lines = [
                "╔══════════════════════════════════════╗",
                "║         ORDER PLACED SUCCESSFULLY    ║",
                "╚══════════════════════════════════════╝",
                f"  Order ID       : {self.order_id}",
                f"  Client OID     : {self.client_order_id}",
                f"  Symbol         : {self.symbol}",
                f"  Side           : {self.side}",
                f"  Type           : {self.order_type}",
                f"  Status         : {self.status}",
                f"  Quantity       : {self.orig_qty}",
                f"  Executed Qty   : {self.executed_qty}",
                f"  Avg Price      : {self.avg_price}",
                f"  Time In Force  : {self.time_in_force}",
            ]
        else:
            lines = [
                "╔══════════════════════════════════════╗",
                "║           ORDER FAILED               ║",
                "╚══════════════════════════════════════╝",
                f"  Error: {self.error_message}",
            ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_response(raw: dict) -> OrderResult:
    """Convert the raw Binance API dict into an ``OrderResult``."""
    return OrderResult(
        success=True,
        order_id=raw.get("orderId"),
        client_order_id=raw.get("clientOrderId"),
        symbol=raw.get("symbol"),
        side=raw.get("side"),
        order_type=raw.get("type"),
        status=raw.get("status"),
        executed_qty=raw.get("executedQty"),
        avg_price=raw.get("avgPrice"),
        orig_qty=raw.get("origQty"),
        time_in_force=raw.get("timeInForce"),
        raw_response=raw,
    )


def _build_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
) -> dict:
    """
    Build the parameter dictionary accepted by the Binance API.

    For LIMIT orders ``timeInForce`` is set to 'GTC' (Good Till Cancelled).
    ``reduceOnly`` is not included so the order can open a new position.
    """
    params: dict = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
    }
    if order_type == "LIMIT":
        params["price"] = price
        params["timeInForce"] = "GTC"

    logger.debug("Built order params: %s", params)
    return params


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def place_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
) -> OrderResult:
    """
    Place a futures order on the Binance Testnet.

    Args:
        symbol:     Trading pair (e.g. 'BTCUSDT').
        side:       'BUY' or 'SELL'.
        order_type: 'MARKET' or 'LIMIT'.
        quantity:   Order size in base asset units.
        price:      Limit price (required for LIMIT orders).

    Returns:
        ``OrderResult`` dataclass — always returned, never raises.
        Check ``.success`` to determine outcome.
    """
    params = _build_params(symbol, side, order_type, quantity, price)

    logger.info(
        "Placing %s %s order | symbol=%s | qty=%s | price=%s",
        side,
        order_type,
        symbol,
        quantity,
        price,
    )

    try:
        client = get_client()
        raw = client.futures_create_order(**params)
        logger.info("Order response received: %s", raw)
        result = _parse_response(raw)
        logger.info(
            "Order placed successfully: orderId=%s, status=%s",
            result.order_id,
            result.status,
        )
        return result

    except BinanceOrderException as exc:
        msg = f"Order rejected by Binance: {exc.message} (code: {exc.code})"
        logger.error(msg)
        return OrderResult(success=False, error_message=msg)

    except BinanceAPIException as exc:
        msg = f"Binance API error: {exc.message} (code: {exc.code}, status: {exc.status_code})"
        logger.error(msg)
        return OrderResult(success=False, error_message=msg)

    except EnvironmentError as exc:
        msg = str(exc)
        logger.error(msg)
        return OrderResult(success=False, error_message=msg)

    except Exception as exc:
        msg = f"Unexpected error while placing order: {exc}"
        logger.exception(msg)
        return OrderResult(success=False, error_message=msg)
