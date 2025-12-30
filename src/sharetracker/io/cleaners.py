from __future__ import annotations

import re
from pathlib import Path
import pandas as pd

_MONEY_RE = re.compile(r"[,\s\$]")
_DOTS_RE = re.compile(r"\.{3,}")  # handles "16...000" corruption


def read_text_safely(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def deellipsis(text: str) -> str:
    return _DOTS_RE.sub("", text)


def money_to_float(x) -> float:
    if pd.isna(x):
        return 0.0
    s = str(x).strip()
    if s == "":
        return 0.0
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = _MONEY_RE.sub("", s)
    try:
        v = float(s)
        return -v if neg else v
    except ValueError:
        return 0.0


def to_float(x) -> float:
    if pd.isna(x):
        return 0.0
    s = str(x).strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0
