from __future__ import annotations

from datetime import datetime
import pandas as pd

from sharetracker.io.cleaners import money_to_float, to_float
from sharetracker.portfolio.models import Transaction, TxType


def _parse_coinspot_dt(s: str) -> datetime:
    return datetime.strptime(str(s).strip(), "%d/%m/%Y %I:%M %p")


def _coin_from_market(market: str) -> tuple[str, str]:
    a, b = str(market).strip().split("/")
    return a.upper(), b.upper()


def load_coinspot_orderhistory(path: str) -> list[Transaction]:
    df = pd.read_csv(path)
    txs: list[Transaction] = []

    for i, r in df.iterrows():
        dt = _parse_coinspot_dt(r["Transaction Date"])
        side = str(r["Type"]).strip().upper()
        coin, mkt = _coin_from_market(r["Market"])

        if mkt != "AUD":
            continue

        qty = to_float(r.get("Amount"))
        price = to_float(r.get("Rate ex. fee")) or to_float(r.get("Rate inc. fee"))
        fee_aud = money_to_float(r.get("Fee AUD (inc GST)"))
        total_aud = money_to_float(r.get("Total AUD"))

        symbol = f"{coin}-AUD"

        if side == "BUY":
            cash_amount = -abs(total_aud) if total_aud != 0 else -(qty * price + fee_aud)
            txs.append(Transaction(
                dt=dt, type=TxType.BUY, symbol=symbol,
                quantity=qty, price=price, fees=abs(fee_aud),
                cash_amount=cash_amount, source="COINSPOT",
                raw_id=f"COINSPOT:{i}", note=f"{coin}/{mkt}"
            ))
        elif side == "SELL":
            cash_amount = abs(total_aud) if total_aud != 0 else (qty * price - fee_aud)
            txs.append(Transaction(
                dt=dt, type=TxType.SELL, symbol=symbol,
                quantity=qty, price=price, fees=abs(fee_aud),
                cash_amount=cash_amount, source="COINSPOT",
                raw_id=f"COINSPOT:{i}", note=f"{coin}/{mkt}"
            ))
    return txs
