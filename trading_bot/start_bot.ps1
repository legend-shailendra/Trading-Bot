###############################################################
#  start_bot.ps1 — Single launcher for CLI and Web UI
#  Usage:
#    .\start_bot.ps1 cli   BTCUSDT BUY MARKET 0.001
#    .\start_bot.ps1 cli   BTCUSDT BUY LIMIT  0.001 --price 62000
#    .\start_bot.ps1 web                         (starts Flask on :5000)
###############################################################

$PYTHON = "C:\Users\shail\OneDrive\Documents\Primetrade\.venv\Scripts\python.exe"

# ── Load credentials from .env file if it exists ────────────
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.+)$") {
            $name  = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"').Trim("'")
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
            Set-Item -Path "Env:$name" -Value $value
        }
    }
    Write-Host "[OK] Credentials loaded from .env" -ForegroundColor Green
} else {
    Write-Host "[WARN] No .env file found. Using existing environment variables." -ForegroundColor Yellow
}

# Verify keys are present
if (-not $env:BINANCE_API_KEY -or -not $env:BINANCE_SECRET_KEY) {
    Write-Host ""
    Write-Host "[ERROR] BINANCE_API_KEY or BINANCE_SECRET_KEY not set." -ForegroundColor Red
    Write-Host "Create a .env file in trading_bot/ with:"
    Write-Host "  BINANCE_API_KEY=your_key_here"
    Write-Host "  BINANCE_SECRET_KEY=your_secret_here"
    exit 1
}

$mode = $args[0]

if ($mode -eq "cli") {
    $cliArgs = $args[1..($args.Length - 1)]
    Write-Host "[Running CLI] place $cliArgs" -ForegroundColor Cyan
    & $PYTHON -m bot.cli place @cliArgs
}
elseif ($mode -eq "web") {
    Write-Host "[Starting Web UI] http://127.0.0.1:5000" -ForegroundColor Cyan
    & $PYTHON app.py
}
else {
    Write-Host "Usage:"
    Write-Host "  .\start_bot.ps1 cli BTCUSDT BUY MARKET 0.001"
    Write-Host "  .\start_bot.ps1 cli BTCUSDT SELL LIMIT 0.001 --price 62000"
    Write-Host "  .\start_bot.ps1 web"
}
