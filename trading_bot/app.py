"""
app.py
------
Lightweight Flask web UI for the Primetrade Trading Bot.

Exposes two routes:
  GET  /          → Renders the order form.
  POST /place     → Validates inputs, places the order, renders the result.
  GET  /health    → Simple JSON health-check endpoint.

Run:
    python app.py
Then open http://localhost:5000 in your browser.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

# Load .env credentials before any bot module imports touch os.environ
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path, override=True)   # always wins over stale shell vars
except ImportError:
    pass  # python-dotenv not installed — fall back to environment variables

from flask import Flask, render_template_string, request, jsonify

from bot.logging_config import logger
from bot.orders import place_order
from bot.validators import validate_all, VALID_SIDES, VALID_ORDER_TYPES

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "primetrade-secret-2024")

# ---------------------------------------------------------------------------
# HTML Template (single-file, no external template folder required)
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Primetrade Bot — Binance Futures Testnet</title>
  <meta name="description" content="Place Market and Limit orders on the Binance Futures Testnet with the Primetrade Trading Bot." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet" />
  <style>
    /* ── CSS Reset & Tokens ─────────────────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg-deep:     #050a14;
      --bg-card:     rgba(12, 20, 38, 0.85);
      --bg-glass:    rgba(255, 255, 255, 0.04);
      --border:      rgba(99, 179, 237, 0.18);
      --border-glow: rgba(99, 179, 237, 0.45);

      --cyan:       #38bdf8;
      --cyan-dark:  #0ea5e9;
      --green:      #4ade80;
      --red:        #f87171;
      --yellow:     #fbbf24;
      --text-1:     #f0f6ff;
      --text-2:     #94a3b8;
      --text-3:     #475569;

      --gradient-hero: linear-gradient(135deg, #0f172a 0%, #0a1628 50%, #0d1f3c 100%);
      --gradient-card: linear-gradient(145deg, rgba(56,189,248,0.06) 0%, rgba(99,102,241,0.04) 100%);
      --gradient-btn:  linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%);
      --gradient-success: linear-gradient(135deg, rgba(74,222,128,0.15) 0%, rgba(16,185,129,0.05) 100%);
      --gradient-error:   linear-gradient(135deg, rgba(248,113,113,0.15) 0%, rgba(239,68,68,0.05) 100%);

      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;

      --shadow-card: 0 8px 32px rgba(0,0,0,0.45), 0 0 0 1px rgba(99,179,237,0.08);
      --shadow-btn:  0 4px 20px rgba(14,165,233,0.35);
      --shadow-input: 0 0 0 1px var(--border), inset 0 1px 2px rgba(0,0,0,0.3);
      --shadow-input-focus: 0 0 0 2px var(--border-glow);
    }

    html { scroll-behavior: smooth; }

    body {
      font-family: 'Inter', system-ui, sans-serif;
      background: var(--gradient-hero);
      min-height: 100vh;
      color: var(--text-1);
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    /* ── Animated background particles ─────────────────────────────── */
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background:
        radial-gradient(ellipse 80% 60% at 20% 10%, rgba(56,189,248,0.08) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 80% 80%, rgba(99,102,241,0.07) 0%, transparent 55%);
      pointer-events: none;
      z-index: 0;
    }

    /* ── Layout ─────────────────────────────────────────────────────── */
    .page-wrapper {
      position: relative;
      z-index: 1;
      width: 100%;
      max-width: 640px;
      padding: 2rem 1.5rem 4rem;
    }

    /* ── Header ─────────────────────────────────────────────────────── */
    header {
      text-align: center;
      margin-bottom: 2.5rem;
      padding-top: 1rem;
    }

    .logo-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(56,189,248,0.1);
      border: 1px solid rgba(56,189,248,0.25);
      border-radius: 100px;
      padding: 6px 16px;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.08em;
      color: var(--cyan);
      text-transform: uppercase;
      margin-bottom: 1rem;
    }

    .logo-badge .dot {
      width: 7px; height: 7px;
      border-radius: 50%;
      background: var(--green);
      box-shadow: 0 0 8px var(--green);
      animation: pulse 2s ease-in-out infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50%       { opacity: 0.6; transform: scale(1.3); }
    }

    h1 {
      font-size: clamp(1.8rem, 5vw, 2.6rem);
      font-weight: 800;
      letter-spacing: -0.03em;
      line-height: 1.1;
      background: linear-gradient(135deg, #fff 20%, var(--cyan) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 0.6rem;
    }

    .subtitle {
      font-size: 0.93rem;
      color: var(--text-2);
      line-height: 1.6;
    }

    /* ── Card ───────────────────────────────────────────────────────── */
    .card {
      background: var(--bg-card);
      background-image: var(--gradient-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 2rem;
      box-shadow: var(--shadow-card);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
    }

    .card-title {
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--cyan);
      margin-bottom: 1.5rem;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .card-title::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--border);
    }

    /* ── Form ───────────────────────────────────────────────────────── */
    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }

    .field {
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-bottom: 1.1rem;
    }

    .field.full { grid-column: 1 / -1; }

    label {
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.05em;
      color: var(--text-2);
      text-transform: uppercase;
    }

    label span.req { color: var(--cyan); margin-left: 2px; }

    input, select {
      background: rgba(255,255,255,0.04);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      color: var(--text-1);
      font-family: 'Inter', sans-serif;
      font-size: 0.95rem;
      padding: 0.65rem 0.9rem;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
      width: 100%;
      -webkit-appearance: none;
    }

    input::placeholder { color: var(--text-3); }

    input:focus, select:focus {
      border-color: var(--cyan-dark);
      box-shadow: var(--shadow-input-focus);
      background: rgba(56,189,248,0.04);
    }

    select option {
      background: #0f172a;
      color: var(--text-1);
    }

    /* ── Toggle chips for SIDE ──────────────────────────────────────── */
    .chip-group {
      display: flex;
      gap: 8px;
    }

    .chip {
      flex: 1;
      padding: 0.6rem;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      background: transparent;
      color: var(--text-2);
      font-family: 'Inter', sans-serif;
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
      text-align: center;
      letter-spacing: 0.04em;
      transition: all 0.18s;
    }

    .chip:hover { border-color: var(--cyan); color: var(--text-1); }

    .chip.active-buy  { background: rgba(74,222,128,0.12); border-color: var(--green); color: var(--green); }
    .chip.active-sell { background: rgba(248,113,113,0.12); border-color: var(--red);  color: var(--red);  }

    input[name="side"] { display: none; }

    /* ── Price field visibility ─────────────────────────────────────── */
    #price-field {
      transition: opacity 0.2s, max-height 0.3s;
      overflow: hidden;
    }

    #price-field.hidden { opacity: 0; max-height: 0; margin-bottom: 0; pointer-events: none; }
    #price-field.visible { opacity: 1; max-height: 120px; }

    /* ── Submit button ──────────────────────────────────────────────── */
    .btn-submit {
      width: 100%;
      padding: 0.85rem 1rem;
      background: var(--gradient-btn);
      border: none;
      border-radius: var(--radius-sm);
      color: #fff;
      font-family: 'Inter', sans-serif;
      font-size: 1rem;
      font-weight: 700;
      letter-spacing: 0.03em;
      cursor: pointer;
      box-shadow: var(--shadow-btn);
      transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s;
      margin-top: 0.5rem;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }

    .btn-submit:hover  { transform: translateY(-1px); box-shadow: 0 6px 28px rgba(14,165,233,0.5); }
    .btn-submit:active { transform: translateY(0);    opacity: 0.85; }

    .btn-submit.loading { opacity: 0.7; cursor: not-allowed; }

    /* ── Result card ────────────────────────────────────────────────── */
    .result-card {
      margin-top: 1.5rem;
      border-radius: var(--radius-md);
      padding: 1.4rem 1.5rem;
      border: 1px solid;
      animation: slide-up 0.35s ease-out both;
    }

    @keyframes slide-up {
      from { opacity: 0; transform: translateY(12px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    .result-card.success {
      background: var(--gradient-success);
      border-color: rgba(74,222,128,0.3);
    }

    .result-card.error {
      background: var(--gradient-error);
      border-color: rgba(248,113,113,0.3);
    }

    .result-status {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 1rem;
    }

    .status-icon {
      width: 36px; height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1rem;
      flex-shrink: 0;
    }

    .status-icon.success { background: rgba(74,222,128,0.2); color: var(--green); }
    .status-icon.error   { background: rgba(248,113,113,0.2); color: var(--red); }

    .status-title {
      font-weight: 700;
      font-size: 1rem;
    }

    .status-title.success { color: var(--green); }
    .status-title.error   { color: var(--red); }

    .result-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.6rem 1.2rem;
    }

    .result-item { display: flex; flex-direction: column; gap: 2px; }
    .result-label { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-3); }
    .result-value {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--text-1);
    }

    .result-value.green { color: var(--green); }
    .result-value.red   { color: var(--red); }
    .result-value.cyan  { color: var(--cyan); }

    .error-message {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.83rem;
      color: var(--red);
      line-height: 1.6;
      word-break: break-all;
    }

    /* ── Footer ─────────────────────────────────────────────────────── */
    footer {
      text-align: center;
      margin-top: 2rem;
      font-size: 0.75rem;
      color: var(--text-3);
      line-height: 1.7;
    }

    footer a { color: var(--cyan); text-decoration: none; }

    /* ── Responsive ─────────────────────────────────────────────────── */
    @media (max-width: 520px) {
      .form-row { grid-template-columns: 1fr; }
      .field.full { grid-column: auto; }
      .result-grid { grid-template-columns: 1fr; }
      .card { padding: 1.4rem; }
    }

    /* ── Order History ───────────────────────────────────────────────── */
    .history-card { margin-top: 1.5rem; }

    .history-toolbar {
      display: flex; align-items: center; gap: 10px; margin-bottom: 1rem;
    }
    .history-toolbar input {
      flex: 1; max-width: 160px;
      padding: 0.45rem 0.75rem;
      font-size: 0.83rem;
    }
    .btn-refresh {
      padding: 0.45rem 1rem;
      background: rgba(56,189,248,0.12);
      border: 1px solid var(--border-glow);
      border-radius: var(--radius-sm);
      color: var(--cyan);
      font-family: 'Inter', sans-serif;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.18s;
    }
    .btn-refresh:hover { background: rgba(56,189,248,0.22); }

    .balance-strip {
      display: flex; gap: 1rem; flex-wrap: wrap;
      margin-bottom: 1rem;
    }
    .balance-pill {
      background: rgba(56,189,248,0.08);
      border: 1px solid var(--border);
      border-radius: 100px;
      padding: 4px 14px;
      font-size: 0.78rem;
      font-family: 'JetBrains Mono', monospace;
      color: var(--cyan);
    }

    .orders-table-wrap { overflow-x: auto; }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.8rem;
    }
    th {
      text-align: left;
      font-size: 0.68rem;
      letter-spacing: 0.07em;
      text-transform: uppercase;
      color: var(--text-3);
      padding: 6px 8px;
      border-bottom: 1px solid var(--border);
    }
    td {
      padding: 7px 8px;
      border-bottom: 1px solid rgba(99,179,237,0.07);
      font-family: 'JetBrains Mono', monospace;
      color: var(--text-2);
      white-space: nowrap;
    }
    tr:last-child td { border-bottom: none; }
    .tag {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 100px;
      font-size: 0.7rem;
      font-weight: 700;
    }
    .tag-filled  { background: rgba(74,222,128,0.15); color: var(--green); }
    .tag-new     { background: rgba(251,191,36,0.15); color: var(--yellow); }
    .tag-canceled{ background: rgba(100,116,139,0.2); color: var(--text-3); }
    .tag-buy     { color: var(--green); }
    .tag-sell    { color: var(--red); }
    #history-status { font-size: 0.78rem; color: var(--text-3); margin-left: auto; }
  </style>
</head>
<body>
  <div class="page-wrapper">

    <!-- ── Header ─────────────────────────────────────────────────── -->
    <header>
      <div class="logo-badge">
        <span class="dot"></span>
        Futures Testnet Live
      </div>
      <h1>Primetrade Bot</h1>
      <p class="subtitle">
        Place <strong>Market</strong> &amp; <strong>Limit</strong> orders on the
        Binance Futures Testnet — zero real funds at risk.
      </p>
    </header>

    <!-- ── Order Form ─────────────────────────────────────────────── -->
    <div class="card">
      <p class="card-title">📋 New Order</p>

      <form id="order-form" method="POST" action="/place" autocomplete="off">

        <!-- Symbol -->
        <div class="field">
          <label for="symbol">Symbol <span class="req">*</span></label>
          <input
            id="symbol" name="symbol" type="text"
            placeholder="e.g. BTCUSDT"
            value="{{ form.symbol or '' }}"
            required
            style="text-transform:uppercase"
          />
        </div>

        <!-- Side + Order Type -->
        <div class="form-row">

          <!-- Side chips -->
          <div class="field">
            <label>Side <span class="req">*</span></label>
            <input type="hidden" id="side-input" name="side" value="{{ form.side or 'BUY' }}" />
            <div class="chip-group" id="side-chips">
              <button type="button" class="chip {% if (form.side or 'BUY') == 'BUY' %}active-buy{% endif %}" data-value="BUY" id="chip-buy">▲ BUY</button>
              <button type="button" class="chip {% if (form.side or 'BUY') == 'SELL' %}active-sell{% endif %}" data-value="SELL" id="chip-sell">▼ SELL</button>
            </div>
          </div>

          <!-- Order type -->
          <div class="field">
            <label for="order_type">Order Type <span class="req">*</span></label>
            <select id="order_type" name="order_type" required>
              <option value="MARKET" {% if (form.order_type or 'MARKET') == 'MARKET' %}selected{% endif %}>Market</option>
              <option value="LIMIT"  {% if (form.order_type or '') == 'LIMIT'  %}selected{% endif %}>Limit</option>
            </select>
          </div>
        </div>

        <!-- Quantity + Price -->
        <div class="form-row">
          <div class="field">
            <label for="quantity">Quantity <span class="req">*</span></label>
            <input
              id="quantity" name="quantity" type="number"
              step="any" min="0.00001"
              placeholder="e.g. 0.001"
              value="{{ form.quantity or '' }}"
              required
            />
          </div>

          <div class="field" id="price-field">
            <label for="price">Limit Price <span class="req">*</span></label>
            <input
              id="price" name="price" type="number"
              step="any" min="0"
              placeholder="e.g. 65000"
              value="{{ form.price or '' }}"
            />
          </div>
        </div>

        <button type="submit" class="btn-submit" id="submit-btn">
          <span id="btn-text">🚀 Place Order</span>
        </button>
      </form>
    </div>

    <!-- ── Result Panel ──────────────────────────────────────────── -->
    {% if result %}
    <div class="result-card {{ 'success' if result.success else 'error' }}">

      {% if result.success %}
      <div class="result-status">
        <div class="status-icon success">✓</div>
        <div>
          <div class="status-title success">Order Placed Successfully</div>
          <div style="font-size:0.78rem; color: var(--text-2); margin-top:2px;">
            {{ timestamp }}
          </div>
        </div>
      </div>

      <div class="result-grid">
        <div class="result-item">
          <span class="result-label">Order ID</span>
          <span class="result-value cyan">{{ result.order_id }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Status</span>
          <span class="result-value green">{{ result.status }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Symbol</span>
          <span class="result-value">{{ result.symbol }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Side</span>
          <span class="result-value {{ 'green' if result.side == 'BUY' else 'red' }}">{{ result.side }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Type</span>
          <span class="result-value">{{ result.order_type }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Time In Force</span>
          <span class="result-value">{{ result.time_in_force or 'N/A' }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Quantity</span>
          <span class="result-value">{{ result.orig_qty }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Executed Qty</span>
          <span class="result-value">{{ result.executed_qty }}</span>
        </div>
        <div class="result-item" style="grid-column: 1 / -1;">
          <span class="result-label">Avg Fill Price</span>
          <span class="result-value cyan">{{ result.avg_price }}</span>
        </div>
      </div>

      {% else %}
      <div class="result-status">
        <div class="status-icon error">✕</div>
        <div>
          <div class="status-title error">Order Failed</div>
          <div style="font-size:0.78rem; color: var(--text-2); margin-top:2px;">
            {{ timestamp }}
          </div>
        </div>
      </div>
      <p class="error-message">{{ result.error_message }}</p>
      {% endif %}

    </div>
    {% endif %}

    <!-- ── Order History ──────────────────────────────────────────── -->
    <div class="card history-card" id="history-panel">
      <p class="card-title">&#x1F4CA; Order History &amp; Balance</p>

      <div class="history-toolbar">
        <input id="hist-symbol" type="text" placeholder="BTCUSDT" value="BTCUSDT"
               style="text-transform:uppercase" />
        <button class="btn-refresh" onclick="loadHistory()">&#x21BB; Refresh</button>
        <span id="history-status">Loading...</span>
      </div>

      <div class="balance-strip" id="balance-strip"></div>

      <div class="orders-table-wrap">
        <table id="orders-table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Side</th>
              <th>Type</th>
              <th>Qty</th>
              <th>Exec Qty</th>
              <th>Avg Price</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id="orders-body">
            <tr><td colspan="7" style="text-align:center;color:var(--text-3)">Loading orders...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Footer ────────────────────────────────────────────────── -->
    <footer>
      Primetrade Bot &nbsp;&middot;&nbsp; Binance Futures Testnet only &nbsp;&middot;&nbsp;
      No real funds at risk.<br />
      <a href="https://testnet.binancefuture.com" target="_blank" rel="noopener">testnet.binancefuture.com</a>
    </footer>

  </div>

  <!-- ── JS: side chips + price field toggle + loading state ──── -->
  <script>
    // ── Side chip toggle ────────────────────────────────────────
    const sideInput = document.getElementById('side-input');
    const chips = document.querySelectorAll('.chip');

    chips.forEach(chip => {
      chip.addEventListener('click', () => {
        chips.forEach(c => c.classList.remove('active-buy', 'active-sell'));
        const val = chip.dataset.value;
        sideInput.value = val;
        chip.classList.add(val === 'BUY' ? 'active-buy' : 'active-sell');
      });
    });

    // ── Price field show/hide ───────────────────────────────────
    const orderTypeSelect = document.getElementById('order_type');
    const priceField      = document.getElementById('price-field');
    const priceInput      = document.getElementById('price');

    function togglePrice() {
      const isLimit = orderTypeSelect.value === 'LIMIT';
      priceField.classList.toggle('hidden', !isLimit);
      priceField.classList.toggle('visible', isLimit);
      priceInput.required = isLimit;
      if (!isLimit) priceInput.value = '';
    }

    orderTypeSelect.addEventListener('change', togglePrice);
    togglePrice(); // run on page load

    // ── Submit loading state ────────────────────────────────────
    document.getElementById('order-form').addEventListener('submit', () => {
      const btn  = document.getElementById('submit-btn');
      const text = document.getElementById('btn-text');
      btn.classList.add('loading');
      btn.disabled = true;
      text.textContent = 'Placing order...';
    });

    // ── Order History loader ────────────────────────────────────
    function statusTag(s) {
      const cls = s === 'FILLED' ? 'tag-filled' : s === 'NEW' ? 'tag-new' : 'tag-canceled';
      return `<span class="tag ${cls}">${s}</span>`;
    }

    async function loadHistory() {
      const sym = document.getElementById('hist-symbol').value.trim().toUpperCase() || 'BTCUSDT';
      document.getElementById('history-status').textContent = 'Fetching...';
      try {
        const res  = await fetch(`/orders?symbol=${sym}&limit=20`);
        const data = await res.json();
        if (data.error) throw new Error(data.error);

        // ── Balance strip ─────────────────────────────────────
        const strip = document.getElementById('balance-strip');
        strip.innerHTML = data.balance.map(b =>
          `<span class="balance-pill">${b.asset}: ${parseFloat(b.balance).toFixed(4)}</span>`
        ).join('');

        // ── Orders table ──────────────────────────────────────
        const tbody = document.getElementById('orders-body');
        if (!data.recent.length) {
          tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-3)">No orders found for ' + sym + '</td></tr>';
        } else {
          tbody.innerHTML = data.recent.map(o => {
            const sideClass = o.side === 'BUY' ? 'tag-buy' : 'tag-sell';
            const avg = parseFloat(o.avgPrice) > 0 ? parseFloat(o.avgPrice).toFixed(2) : '-';
            return `<tr>
              <td style="color:var(--cyan)">${o.orderId}</td>
              <td class="${sideClass}" style="font-weight:700">${o.side}</td>
              <td>${o.type}</td>
              <td>${o.origQty}</td>
              <td>${o.executedQty}</td>
              <td>${avg}</td>
              <td>${statusTag(o.status)}</td>
            </tr>`;
          }).join('');
        }

        document.getElementById('history-status').textContent =
          `Updated ${data.timestamp} | ${data.recent.length} orders`;

      } catch(err) {
        document.getElementById('history-status').textContent = 'Error: ' + err.message;
        document.getElementById('orders-body').innerHTML =
          `<tr><td colspan="7" style="color:var(--red)">${err.message}</td></tr>`;
      }
    }

    // Auto-load on page open + refresh after each order placement
    loadHistory();
    // Also refresh when symbol input changes (debounced)
    document.getElementById('hist-symbol').addEventListener('input', () => {
      clearTimeout(window._histTimer);
      window._histTimer = setTimeout(loadHistory, 600);
    });
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    """Render the empty order form."""
    logger.info("GET / — rendering order form")
    return render_template_string(HTML_TEMPLATE, result=None, form={}, timestamp=None)


@app.route("/place", methods=["POST"])
def place():
    """Validate form inputs, place the order, render the result."""
    form_data = {
        "symbol":     request.form.get("symbol", "").strip(),
        "side":       request.form.get("side", "").strip(),
        "order_type": request.form.get("order_type", "").strip(),
        "quantity":   request.form.get("quantity", "").strip(),
        "price":      request.form.get("price", "").strip() or None,
    }

    logger.info("POST /place — form data: %s", form_data)

    # Convert to appropriate types before validation
    raw_quantity = form_data["quantity"]
    raw_price = form_data["price"]

    try:
        quantity = float(raw_quantity)
    except (TypeError, ValueError):
        quantity = None

    try:
        price = float(raw_price) if raw_price is not None else None
    except (TypeError, ValueError):
        price = None

    # Validate
    try:
        validated = validate_all(
            symbol=form_data["symbol"],
            side=form_data["side"],
            order_type=form_data["order_type"],
            quantity=quantity,
            price=price,
        )
    except ValueError as exc:
        logger.warning("Validation error from web form: %s", exc)
        from bot.orders import OrderResult
        result = OrderResult(success=False, error_message=str(exc))
        return render_template_string(
            HTML_TEMPLATE,
            result=result,
            form=form_data,
            timestamp=_now(),
        ), 400

    # Place the order
    result = place_order(
        symbol=validated["symbol"],
        side=validated["side"],
        order_type=validated["order_type"],
        quantity=validated["quantity"],
        price=validated["price"],
    )

    status_code = 200 if result.success else 502
    return render_template_string(
        HTML_TEMPLATE,
        result=result,
        form={
            "symbol":     validated["symbol"],
            "side":       validated["side"],
            "order_type": validated["order_type"],
            "quantity":   validated["quantity"],
            "price":      validated["price"],
        },
        timestamp=_now(),
    ), status_code


@app.route("/health", methods=["GET"])
def health():
    """Simple health-check used by monitoring tools."""
    return jsonify({"status": "ok", "service": "primetrade-bot", "timestamp": _now()})


@app.route("/orders", methods=["GET"])
def orders():
    """Return recent orders + balance from the Futures Testnet as JSON."""
    symbol = request.args.get("symbol", "BTCUSDT").upper()
    limit  = min(int(request.args.get("limit", 20)), 50)
    try:
        from bot.client import get_client
        client = get_client()
        recent = client.futures_get_all_orders(symbol=symbol, limit=limit)
        recent.reverse()   # newest first
        open_o = client.futures_get_open_orders()
        balance_raw = client.futures_account_balance()
        balance = [
            {"asset": b["asset"], "balance": b["balance"], "available": b["availableBalance"]}
            for b in balance_raw if float(b["balance"]) > 0
        ]
        return jsonify({
            "symbol":      symbol,
            "recent":      recent,
            "open_orders": open_o,
            "balance":     balance,
            "timestamp":   _now(),
        })
    except Exception as exc:
        logger.error("Error fetching orders: %s", exc)
        return jsonify({"error": str(exc)}), 502


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    logger.info("Starting Primetrade web UI on http://0.0.0.0:%s (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)
