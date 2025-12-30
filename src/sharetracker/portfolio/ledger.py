from __future__ import annotations

from collections import defaultdict
import pandas as pd
from sharetracker.portfolio.models import Transaction, TxType


def build_daily_holdings(txs: list[Transaction], start: str, end: str) -> pd.DataFrame:
    idx = pd.bdate_range(start=start, end=end)
    symbols = sorted({t.symbol for t in txs if t.symbol})
    df = pd.DataFrame(index=idx, columns=["cash"] + symbols, dtype="float64")
    df.loc[:, :] = 0.0

    cash = 0.0
    pos = defaultdict(float)

    txs_sorted = sorted(txs, key=lambda x: x.dt)
    j = 0

    for d in idx:
        while j < len(txs_sorted) and pd.Timestamp(txs_sorted[j].dt) <= d:
            t = txs_sorted[j]
            cash += float(t.cash_amount)
            if t.type == TxType.BUY and t.symbol:
                pos[t.symbol] += t.quantity
            elif t.type == TxType.SELL and t.symbol:
                pos[t.symbol] -= t.quantity
            j += 1

        df.at[d, "cash"] = cash
        for sym in symbols:
            df.at[d, sym] = pos.get(sym, 0.0)

    return df
