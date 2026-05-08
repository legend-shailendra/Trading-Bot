"""
validators.py
-------------
Pure input-validation logic — no Binance API calls here.
All functions raise ValueError with descriptive messages on failure.
"""

from __future__ import annotations

from typing import Optional

from bot.logging_config import logger

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


def validate_symbol(symbol: str) -> str:
    """
    Normalise and validate the trading pair symbol.

    Args:
        symbol: Raw symbol string (e.g. 'btcusdt', 'BTCUSDT').

    Returns:
        Upper-cased symbol string.

    Raises:
        ValueError: If the symbol is empty or contains invalid characters.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be empty.")
    if not symbol.isalpha():
        raise ValueError(
            f"Symbol '{symbol}' contains invalid characters. "
            "Expected letters only, e.g. BTCUSDT."
        )
    logger.debug("Symbol validated: %s", symbol)
    return symbol


def validate_side(side: str) -> str:
    """
    Validate and normalise the order side.

    Args:
        side: 'BUY' or 'SELL' (case-insensitive).

    Returns:
        Upper-cased side string.

    Raises:
        ValueError: If side is not BUY or SELL.
    """
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    logger.debug("Side validated: %s", side)
    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate and normalise the order type.

    Args:
        order_type: 'MARKET' or 'LIMIT' (case-insensitive).

    Returns:
        Upper-cased order type string.

    Raises:
        ValueError: If type is not MARKET or LIMIT.
    """
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    logger.debug("Order type validated: %s", order_type)
    return order_type


def validate_quantity(quantity: float) -> float:
    """
    Validate the order quantity.

    Args:
        quantity: Desired quantity (must be > 0).

    Returns:
        Validated quantity as float.

    Raises:
        ValueError: If quantity is zero or negative.
    """
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity '{quantity}' is not a valid number.")

    if quantity <= 0:
        raise ValueError(f"Quantity must be greater than zero, got {quantity}.")
    logger.debug("Quantity validated: %s", quantity)
    return quantity


def validate_price(price: Optional[float], order_type: str) -> Optional[float]:
    """
    Validate the order price.

    For LIMIT orders the price is mandatory and must be > 0.
    For MARKET orders the price must be None / not provided.

    Args:
        price: Price value or None.
        order_type: Normalised order type string ('MARKET' or 'LIMIT').

    Returns:
        Validated price as float, or None for MARKET orders.

    Raises:
        ValueError: On invalid price for LIMIT orders or unexpected
                    price provided for MARKET orders.
    """
    order_type = order_type.strip().upper()

    if order_type == "LIMIT":
        if price is None:
            raise ValueError("Price is required for LIMIT orders.")
        try:
            price = float(price)
        except (TypeError, ValueError):
            raise ValueError(f"Price '{price}' is not a valid number.")
        if price <= 0:
            raise ValueError(f"Price must be greater than zero, got {price}.")
        logger.debug("Price validated for LIMIT order: %s", price)
        return price

    # MARKET orders — price is ignored
    if price is not None:
        logger.warning(
            "Price '%s' was provided for a MARKET order and will be ignored.", price
        )
    return None


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
) -> dict:
    """
    Run all validators and return a clean parameter dict.

    Args:
        symbol: Trading pair symbol.
        side: Order side.
        order_type: Order type.
        quantity: Order quantity.
        price: Order price (required for LIMIT, None for MARKET).

    Returns:
        Dictionary of validated parameters ready to pass to the order handler.

    Raises:
        ValueError: If any individual validation fails.
    """
    validated = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
    }
    validated["price"] = validate_price(price, validated["order_type"])
    logger.info("All inputs validated successfully: %s", validated)
    return validated
