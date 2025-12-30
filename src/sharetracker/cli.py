from __future__ import annotations

from datetime import datetime
import pandas as pd
import typer

from sharetracker.config import load_config
from sharetracker.io.cmc_cash_summary import load_cmc_cash_transaction_summary
from sharetracker.io.cmc_confirmation import load_cmc_confirmation
from sharetracker.io.betashares_transactions import load_betashares_transactions
from sharetracker.io.coinspot_orderhistory import load_coinspot_orderhistory
from sharetracker.io.normalize import apply_symbol_map, sort_and_dedupe, to_dataframe
from sharetracker.pricing.yahoo import PriceCache
from sharetracker.portfolio.ledger import build_daily_holdings
from sharetracker.analytics.performance import summary_stats, returns_from_equity
from sharetracker.analytics.benchmark import beta_alpha
from sharetracker.reporting.tax_au import realized_gains_fifo, realized_to_tax_table
from sharetracker.viz.charts import save_equity_curve_chart, save_drawdown_chart

app = typer.Typer(no_args_is_help=True)


@app.command()
def run(
    config: str = typer.Option("configs/config.yml", help="Path to YAML config"),
    start: str = typer.Option("2024-07-01", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(None, help="End date (YYYY-MM-DD), default today"),
    cmc_cash: str = typer.Option(None, help="CMC CashTransactionSummary CSV path"),
    cmc_conf: str = typer.Option(None, help="CMC Confirmation CSV path"),
    betashares: str = typer.Option(None, help="Betashares transactions CSV path"),
    coinspot_orders: str = typer.Option(None, help="CoinSpot orderhistory CSV path"),
):
    cfg = load_config(config)
    end = end or datetime.today().date().isoformat()

    cfg.processed_dir.mkdir(parents=True, exist_ok=True)
    (cfg.outputs_dir / "reports").mkdir(parents=True, exist_ok=True)
    (cfg.outputs_dir / "charts").mkdir(parents=True, exist_ok=True)

    # 1) Ingest
    txs = []
    if cmc_cash:
        txs += load_cmc_cash_transaction_summary(cmc_cash)
    if cmc_conf:
        txs += load_cmc_confirmation(cmc_conf)
    if betashares:
        txs += load_betashares_transactions(betashares)
    if coinspot_orders:
        txs += load_coinspot_orderhistory(coinspot_orders)

    # 2) Normalize
    txs = apply_symbol_map(txs, cfg.symbol_map)
    txs = sort_and_dedupe(txs)
    tx_df = to_dataframe(txs)
    tx_df.to_csv(cfg.processed_dir / "transactions_normalized.csv", index=False)

    # 3) Daily holdings
    holdings = build_daily_holdings(txs, start=start, end=end)

    # 4) Pricing (Yahoo)
    tickers = [c for c in holdings.columns if c != "cash"]
    cache = PriceCache(cache_dir=cfg.processed_dir / "price_cache")

    prices = {t: cache.load_or_fetch(t, start=start, end=end) for t in tickers}
    px_df = pd.DataFrame(prices).reindex(holdings.index).ffill()
    px_df.to_parquet(cfg.processed_dir / "prices.parquet")

    # 5) Equity curve
    equity = holdings["cash"].copy()
    for t in tickers:
        equity = equity + holdings[t] * px_df[t]
    equity.name = "portfolio"

    # 6) Benchmark curve
    bench_px = cache.load_or_fetch(cfg.benchmark_ticker, start=start, end=end).reindex(holdings.index).ffill()
    bench_equity = (bench_px / bench_px.iloc[0]) * float(equity.iloc[0])
    bench_equity.name = "benchmark"

    # 7) Risk/return stats
    port_stats = summary_stats(equity)
    bench_stats = summary_stats(bench_equity)

    port_r = returns_from_equity(equity)
    bench_r = returns_from_equity(bench_equity)
    ba = beta_alpha(port_r, bench_r)

    stats_df = pd.DataFrame([{
        **{f"portfolio_{k}": v for k, v in port_stats.items()},
        **{f"benchmark_{k}": v for k, v in bench_stats.items()},
        **ba,
    }])
    stats_df.to_csv(cfg.outputs_dir / "reports" / "performance_summary.csv", index=False)

    # 8) AU FIFO CGT (BUY/SELL only)
    realized = realized_gains_fifo(txs)
    tax_df = realized_to_tax_table(realized)
    tax_df.to_csv(cfg.outputs_dir / "reports" / "au_cgt_fifo.csv", index=False)

    # 9) Charts
    curve_df = pd.concat([equity, bench_equity], axis=1)
    save_equity_curve_chart(curve_df, cfg.outputs_dir / "charts" / "equity_curve.html", "Equity curve vs benchmark")
    save_drawdown_chart(equity, cfg.outputs_dir / "charts" / "drawdown.html", "Portfolio drawdown")

    typer.echo(f"Wrote: {cfg.processed_dir / 'transactions_normalized.csv'}")
    typer.echo(f"Wrote: {cfg.outputs_dir / 'reports' / 'performance_summary.csv'}")
    typer.echo(f"Wrote: {cfg.outputs_dir / 'reports' / 'au_cgt_fifo.csv'}")
    typer.echo(f"Wrote charts: {cfg.outputs_dir / 'charts'}")


if __name__ == "__main__":
    app()
