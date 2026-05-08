"""
cli.py
------
Command-Line Interface entry point for the Primetrade Trading Bot.

Usage examples
--------------
# Market BUY
python -m bot.cli place BTCUSDT BUY MARKET 0.001

# Limit SELL
python -m bot.cli place BTCUSDT SELL LIMIT 0.001 --price 65000

# Via installed script (see setup / requirements)
trade place BTCUSDT BUY MARKET 0.001
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from bot.logging_config import logger
from bot.orders import place_order
from bot.validators import validate_all


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trade",
        description=(
            "Primetrade Bot — Binance Futures Testnet Order Placer\n\n"
            "Place MARKET or LIMIT orders on BTCUSDT, ETHUSDT, and more."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m bot.cli place BTCUSDT BUY MARKET 0.001\n"
            "  python -m bot.cli place ETHUSDT SELL LIMIT 0.01 --price 3200\n"
        ),
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # --- 'place' sub-command -----------------------------------------------
    place_cmd = sub.add_parser(
        "place",
        help="Place a new futures order.",
        description="Place a Market or Limit order on the Binance Futures Testnet.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    place_cmd.add_argument(
        "symbol",
        type=str,
        help="Trading pair symbol, e.g. BTCUSDT.",
    )
    place_cmd.add_argument(
        "side",
        type=str,
        choices=["BUY", "SELL", "buy", "sell"],
        metavar="SIDE",
        help="Order side: BUY or SELL.",
    )
    place_cmd.add_argument(
        "order_type",
        type=str,
        choices=["MARKET", "LIMIT", "market", "limit"],
        metavar="ORDER_TYPE",
        help="Order type: MARKET or LIMIT.",
    )
    place_cmd.add_argument(
        "quantity",
        type=float,
        help="Order quantity in base asset units (e.g. 0.001 for 0.001 BTC).",
    )
    place_cmd.add_argument(
        "--price",
        "-p",
        type=float,
        default=None,
        dest="price",
        help="Limit price (required for LIMIT orders, ignored for MARKET).",
    )

    return parser


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

def _handle_place(args: argparse.Namespace) -> int:
    """
    Validate inputs and dispatch an order.

    Returns:
        0 on success, 1 on failure.
    """
    # --- Print request summary ---------------------------------------------
    # Force UTF-8 output on Windows to avoid cp1252 emoji encoding errors
    import sys, io
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("\n" + "=" * 42)
    print("  [*]  ORDER REQUEST SUMMARY")
    print("=" * 42)
    print(f"  Symbol     : {args.symbol.upper()}")
    print(f"  Side       : {args.side.upper()}")
    print(f"  Type       : {args.order_type.upper()}")
    print(f"  Quantity   : {args.quantity}")
    price_display = f"{args.price}" if args.price is not None else "N/A (MARKET)"
    print(f"  Price      : {price_display}")
    print("=" * 42 + "\n")

    # --- Validate ----------------------------------------------------------
    try:
        validated = validate_all(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
    except ValueError as exc:
        print(f"[FAIL] Validation error: {exc}\n")
        logger.error("CLI validation error: %s", exc)
        return 1

    # --- Place order -------------------------------------------------------
    result = place_order(
        symbol=validated["symbol"],
        side=validated["side"],
        order_type=validated["order_type"],
        quantity=validated["quantity"],
        price=validated["price"],
    )

    # --- Print result ------------------------------------------------------
    print(result.summary())

    if result.success:
        print("\n[OK] Order placed successfully!\n")
        return 0
    else:
        print("\n[FAIL] Order placement failed.\n")
        return 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "place":
        exit_code = _handle_place(args)
        sys.exit(exit_code)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
