from __future__ import annotations

from datetime import datetime
import pandas as pd

from sharetracker.io.cleaners import money_to_float
from sharetracker.portfolio.models import Transaction, TxType


def load_cmc_cash_transaction_summary(path: str) -> list[Transaction]:
    df = pd.read_csv(path)
    txs: list[Transaction] = []

    for i, r in df.iterrows():
        dt = datetime.strptime(str(r["Date"]).strip(), "%d/%m/%Y")
        desc = str(r.get("Description", "")).strip()

        debit = money_to_float(r.get("Debit $"))
        credit = money_to_float(r.get("Credit $"))
        cash_effect = credit - debit  # + increases cash

        if "OPENING BALANCE" in desc.upper():
            continue

        ttype = TxType.CASH_IN if cash_effect > 0 else TxType.CASH_OUT
        txs.append(
            Transaction(
                dt=dt,
                type=ttype,
                symbol=None,
                cash_amount=cash_effect,
                source="CMC_CASH",
                raw_id=f"CMC_CASH:{i}",
                note=desc,
            )
        )
    return txs
