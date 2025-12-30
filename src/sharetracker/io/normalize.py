from __future__ import annotations

import pandas as pd
from sharetracker.portfolio.models import Transaction


def apply_symbol_map(txs: list[Transaction], symbol_map: dict[str, str]) -> list[Transaction]:
    out: list[Transaction] = []
    for t in txs:
        if t.symbol is None:
            out.append(t)
            continue
        mapped = symbol_map.get(t.symbol, t.symbol)
        if mapped != t.symbol:
            out.append(Transaction(**{**t.__dict__, "symbol": mapped}))
        else:
            out.append(t)
    return out


def sort_and_dedupe(txs: list[Transaction]) -> list[Transaction]:
    seen = set()
    out = []
    for t in sorted(txs, key=lambda x: (x.dt, x.source, x.raw_id)):
        k = (t.dt, t.type, t.symbol, round(t.quantity, 10), round(t.price, 10),
             round(t.fees, 10), round(t.cash_amount, 10), t.source, t.raw_id)
        if k in seen:
            continue
        seen.add(k)
        out.append(t)
    return out


def to_dataframe(txs: list[Transaction]) -> pd.DataFrame:
    return pd.DataFrame([{
        "dt": t.dt,
        "type": t.type.value,
        "symbol": t.symbol,
        "quantity": t.quantity,
        "price": t.price,
        "fees": t.fees,
        "cash_amount": t.cash_amount,
        "source": t.source,
        "raw_id": t.raw_id,
        "note": t.note,
    } for t in txs]).sort_values(["dt", "source", "raw_id"]).reset_index(drop=True)
