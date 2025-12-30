from __future__ import annotations

from datetime import datetime
import io
import pandas as pd

from sharetracker.io.cleaners import read_text_safely, deellipsis, to_float
from sharetracker.portfolio.models import Transaction, TxType


def load_cmc_confirmation(path: str) -> list[Transaction]:
    raw = deellipsis(read_text_safely(path))
    df = pd.read_csv(io.StringIO(raw))

    col_trade_date = "Trade Date" if "Trade Date" in df.columns else None
    col_side = "Order Type" if "Order Type" in df.columns else (
        "Confirmation Number" if "Confirmation Number" in df.columns else None
    )
    col_symbol = "AsxCode" if "AsxCode" in df.columns else ("Symbol" if "Symbol" in df.columns else None)

    if not (col_trade_date and col_side and col_symbol):
        return []

    txs: list[Transaction] = []

    for i, r in df.iterrows():
        dt_raw = str(r[col_trade_date]).strip()
        if not dt_raw or dt_raw.lower() == "nan":
            continue

        try:
            dt = datetime.fromisoformat(dt_raw)
        except ValueError:
            dt = datetime.strptime(dt_raw, "%d/%m/%Y")

        side = str(r[col_side]).strip().upper()
        symbol = str(r[col_symbol]).strip()

        qty = to_float(r.get("Quantity"))
        price = to_float(r.get("Price"))

        brokerage = to_float(r.get("Brokerage")) + to_float(r.get("GST"))
        brokerage += to_float(r.get("OtherCharge")) + to_float(r.get("Fee"))

        if "BUY" in side:
            cash_amount = -(qty * price + brokerage)
            txs.append(Transaction(
                dt=dt, type=TxType.BUY, symbol=symbol,
                quantity=qty, price=price, fees=brokerage,
                cash_amount=cash_amount, source="CMC_CONF",
                raw_id=f"CMC_CONF:{i}"
            ))
        elif "SELL" in side:
            cash_amount = (qty * price - brokerage)
            txs.append(Transaction(
                dt=dt, type=TxType.SELL, symbol=symbol,
                quantity=qty, price=price, fees=brokerage,
                cash_amount=cash_amount, source="CMC_CONF",
                raw_id=f"CMC_CONF:{i}"
            ))
    return txs
