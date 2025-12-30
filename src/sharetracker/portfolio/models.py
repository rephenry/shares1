from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TxType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    CASH_IN = "CASH_IN"
    CASH_OUT = "CASH_OUT"
    FEE = "FEE"


@dataclass(frozen=True)
class Transaction:
    dt: datetime
    type: TxType
    symbol: Optional[str]
    quantity: float = 0.0
    price: float = 0.0
    fees: float = 0.0
    cash_amount: float = 0.0
    source: str = ""
    raw_id: str = ""
    note: str = ""


@dataclass
class Lot:
    symbol: str
    acquired_dt: datetime
    quantity: float
    cost_base_total: float
