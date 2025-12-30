# Share Tracker (ASX + Crypto)

End-to-end portfolio tracker for:
- CMC: cash transaction summary + confirmations
- Betashares: transactions CSV
- CoinSpot: order history CSV
- Pricing: Yahoo Finance (incl. crypto tickers like BTC-AUD)
- Outputs: equity curve, benchmark comparison, risk/return stats, AU FIFO CGT table, charts (HTML)

## Setup
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -e .
```

## Configure
Copy and edit:
- `configs/config.example.yml` -> `configs/config.yml` (do not commit)

## Run (single script)
```bash
python run_all.py --config configs/config.yml --start 2024-07-01 \
  --cmc-cash "data/raw/CashTransactionSummary.csv" \
  --cmc-conf "data/raw/Confirmation.csv" \
  --betashares "data/raw/betashares-transactions.csv" \
  --coinspot-orders "data/raw/orderhistory.csv"
```

## Outputs
- `data/processed/transactions_normalized.csv`
- `outputs/reports/performance_summary.csv`
- `outputs/reports/au_cgt_fifo.csv`
- `outputs/charts/equity_curve.html`
- `outputs/charts/drawdown.html`

## Notes / Best practice (AU tax)
This repo computes FIFO realized gains from BUY/SELL trades.
To be “tax complete” you will typically need additional imports:
- distributions/dividends (incl. franking)
- AMIT cost base adjustments (ETF tax statements)
- crypto deposits/withdrawals, staking rewards, swaps (crypto-to-crypto)
