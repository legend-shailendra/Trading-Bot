###############################################################
#  Primetrade Bot - Full CLI Requirements Demo
#  Run: .\run_demo.ps1 [YOUR_API_KEY] [YOUR_SECRET_KEY]
###############################################################

$PYTHON = "C:\Users\shail\OneDrive\Documents\Primetrade\.venv\Scripts\python.exe"

# Accept keys as arguments or fall back to env vars
$env:BINANCE_API_KEY    = if ($args[0]) { $args[0] } else { $env:BINANCE_API_KEY }
$env:BINANCE_SECRET_KEY = if ($args[1]) { $args[1] } else { $env:BINANCE_SECRET_KEY }

function Banner($text) {
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "  $text" -ForegroundColor Yellow
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

# ── REQ 3 & 4: CLI args + output ────────────────────────────

Banner "REQ 1+2+3+4 | Market BUY (BTCUSDT)"
& $PYTHON -m bot.cli place BTCUSDT BUY MARKET 0.001

Banner "REQ 1+2+3+4 | Market SELL (ETHUSDT)"
& $PYTHON -m bot.cli place ETHUSDT SELL MARKET 0.01

Banner "REQ 1+2+3+4 | Limit BUY with --price (BTCUSDT)"
& $PYTHON -m bot.cli place BTCUSDT BUY LIMIT 0.001 --price 62000

Banner "REQ 1+2+3+4 | Limit SELL with -p shorthand (ETHUSDT)"
& $PYTHON -m bot.cli place ETHUSDT SELL LIMIT 0.01 -p 3200

# ── REQ 3 (validation) + REQ 5 (exception handling) ─────────

Banner "REQ 3+5 | VALIDATION: LIMIT order missing price"
& $PYTHON -m bot.cli place BTCUSDT BUY LIMIT 0.001
# Expected: validation error - price required for LIMIT

Banner "REQ 3+5 | VALIDATION: Invalid side"
& $PYTHON -m bot.cli place BTCUSDT HOLD MARKET 0.001
# Expected: validation error - side must be BUY or SELL

Banner "REQ 3+5 | VALIDATION: Negative quantity"
& $PYTHON -m bot.cli place BTCUSDT BUY MARKET -- -5
# Expected: validation error - quantity must be > 0

Banner "REQ 3+5 | VALIDATION: Invalid symbol characters"
& $PYTHON -m bot.cli place BTC-USDT BUY MARKET 0.001
# Expected: validation error - letters only

# ── REQ 5: Log file ─────────────────────────────────────────

Banner "REQ 5 | LOGGING: Last 20 lines of trading_bot.log"
Get-Content "trading_bot.log" -Tail 20 -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host $_ -ForegroundColor Gray
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Demo complete. All 5 requirements exercised." -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host ""
