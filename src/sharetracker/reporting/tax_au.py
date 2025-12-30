from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd

from sharetracker.portfolio.models import Transaction, TxType, Lot


@dataclass
class RealizedLine:
    symbol: str
    acquired_dt: datetime
    disposed_dt: datetime
    quantity: float
    proceeds: float
    cost_base: float
    gain: float
    discount_eligible: bool


def _au_fin_year(dt: datetime) -> int:
    return dt.year + 1 if (dt.month, dt.day) >= (7, 1) else dt.year


def realized_gains_fifo(txs: list[Transaction]) -> list[RealizedLine]:
    lots: dict[str, list[Lot]] = {}
    realized: list[RealizedLine] = []

    for t in sorted(txs, key=lambda x: x.dt):
        if not t.symbol:
            continue
        sym = t.symbol

        if t.type == TxType.BUY:
            lots.setdefault(sym, []).append(
                Lot(sym, t.dt, t.quantity, (t.quantity * t.price) + t.fees)
            )

        elif t.type == TxType.SELL:
            qty_to_match = t.quantity
            proceeds_total = (t.quantity * t.price) - t.fees

            if sym not in lots or sum(l.quantity for l in lots[sym]) + 1e-12 < qty_to_match:
                print(f"Warning: Insufficient holdings to sell {qty_to_match} of {sym} on {t.dt}; skipping")
                continue

            while qty_to_match > 1e-12:
                lot = lots[sym][0]
                take = min(lot.quantity, qty_to_match)

                cost_portion = lot.cost_base_total * (take / lot.quantity)
                proceeds_portion = proceeds_total * (take / t.quantity)
                gain = proceeds_portion - cost_portion
                discount_eligible = (t.dt - lot.acquired_dt) >= timedelta(days=365)

                realized.append(
                    RealizedLine(sym, lot.acquired_dt, t.dt, take, proceeds_portion, cost_portion, gain, discount_eligible)
                )

                lot.quantity -= take
                lot.cost_base_total -= cost_portion
                qty_to_match -= take

                if lot.quantity <= 1e-12:
                    lots[sym].pop(0)

    return realized


def realized_to_tax_table(realized: list[RealizedLine]) -> pd.DataFrame:
    df = pd.DataFrame([{
        "symbol": r.symbol,
        "acquired_date": r.acquired_dt.date().isoformat(),
        "disposed_date": r.disposed_dt.date().isoformat(),
        "fy": _au_fin_year(r.disposed_dt),
        "quantity": r.quantity,
        "proceeds": r.proceeds,
        "cost_base": r.cost_base,
        "capital_gain": r.gain,
        "discount_eligible": r.discount_eligible,
    } for r in realized])

    if df.empty:
        return df

    df["capital_gain_discounted_component"] = df.apply(
        lambda x: x["capital_gain"] if (x["capital_gain"] > 0 and x["discount_eligible"]) else 0.0, axis=1
    )
    df["capital_gain_other_component"] = df.apply(
        lambda x: x["capital_gain"] if not (x["capital_gain"] > 0 and x["discount_eligible"]) else 0.0, axis=1
    )
    return df.sort_values(["fy", "disposed_date", "symbol"])
