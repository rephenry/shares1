from __future__ import annotations

from datetime import datetime
import pandas as pd

from sharetracker.io.cleaners import money_to_float, to_float
from sharetracker.portfolio.models import Transaction, TxType


def load_betashares_transactions(path: str) -> list[Transaction]:
    df = pd.read_csv(path)
    txs: list[Transaction] = []

    for i, r in df.iterrows():
        dt = datetime.strptime(str(r["Effective Date"]).strip(), "%d/%m/%Y")
        activity = str(r.get("Activity Type", "")).strip()
        symbol = r.get("Symbol")
        symbol = None if pd.isna(symbol) else str(symbol).strip()

        gross = money_to_float(r.get("Gross"))
        brokerage = money_to_float(r.get("Brokerage"))
        price = money_to_float(r.get("Price"))
        qty = to_float(r.get("Quantity"))

        act_u = activity.upper()

        if "DEPOSIT" in act_u:
            txs.append(Transaction(
                dt=dt, type=TxType.CASH_IN, symbol=None,
                cash_amount=abs(gross), source="BETASHARES",
                raw_id=f"BETASHARES:{i}", note=activity
            ))
            continue

        if "WITHDRAW" in act_u:
            txs.append(Transaction(
                dt=dt, type=TxType.CASH_OUT, symbol=None,
                cash_amount=-abs(gross), source="BETASHARES",
                raw_id=f"BETASHARES:{i}", note=activity
            ))
            continue

        if "(BUY)" in act_u or act_u.startswith("BUY"):
            cash_amount = gross if gross != 0 else -(qty * price + brokerage)
            txs.append(Transaction(
                dt=dt, type=TxType.BUY, symbol=symbol,
                quantity=qty, price=price, fees=brokerage,
                cash_amount=cash_amount, source="BETASHARES",
                raw_id=f"BETASHARES:{i}", note=activity
            ))
            continue

        if "(SELL)" in act_u or act_u.startswith("SELL"):
            cash_amount = gross if gross != 0 else (qty * price - brokerage)
            txs.append(Transaction(
                dt=dt, type=TxType.SELL, symbol=symbol,
                quantity=qty, price=price, fees=brokerage,
                cash_amount=cash_amount, source="BETASHARES",
                raw_id=f"BETASHARES:{i}", note=activity
            ))
            continue

        if brokerage:
            txs.append(Transaction(
                dt=dt, type=TxType.FEE, symbol=None,
                fees=abs(brokerage), cash_amount=-abs(brokerage),
                source="BETASHARES", raw_id=f"BETASHARES:{i}", note=activity
            ))
    return txs
