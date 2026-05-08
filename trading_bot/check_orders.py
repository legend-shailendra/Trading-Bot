"""Quick script to verify orders on the Binance Futures Testnet."""
import sys
sys.path.insert(0, ".")
from bot.client import get_client

client = get_client()

# ── Open orders ────────────────────────────────────────────────────────────
open_orders = client.futures_get_open_orders()
print(f"\nOpen orders on testnet: {len(open_orders)}")
for o in open_orders[:10]:
    print(f"  [{o['symbol']}] {o['side']} {o['type']} qty={o['origQty']} "
          f"price={o['price']} status={o['status']} id={o['orderId']}")

# ── Recent BTCUSDT orders ──────────────────────────────────────────────────
print("\nRecent BTCUSDT orders (last 10):")
all_orders = client.futures_get_all_orders(symbol="BTCUSDT", limit=10)
for o in all_orders:
    print(f"  id={o['orderId']} {o['side']} {o['type']} "
          f"qty={o['origQty']} executedQty={o['executedQty']} "
          f"avgPrice={o['avgPrice']} status={o['status']}")

# ── Account balance ────────────────────────────────────────────────────────
print("\nFutures Testnet Account Balance:")
account = client.futures_account_balance()
for b in account:
    if float(b['balance']) > 0:
        print(f"  {b['asset']}: {b['balance']} (available: {b['availableBalance']})")
