from __future__ import annotations

import numpy as np
import pandas as pd


def returns_from_equity(equity: pd.Series) -> pd.Series:
    return equity.pct_change().fillna(0.0)


def annualized_return(daily_returns: pd.Series, periods_per_year: int = 252) -> float:
    growth = (1.0 + daily_returns).prod()
    n = daily_returns.shape[0]
    return float(growth ** (periods_per_year / max(n, 1)) - 1.0)


def annualized_vol(daily_returns: pd.Series, periods_per_year: int = 252) -> float:
    return float(daily_returns.std(ddof=1) * np.sqrt(periods_per_year))


def sharpe(daily_returns: pd.Series, rf: float = 0.0, periods_per_year: int = 252) -> float:
    rf_daily = (1.0 + rf) ** (1.0 / periods_per_year) - 1.0
    ex = daily_returns - rf_daily
    vol = ex.std(ddof=1)
    return 0.0 if vol == 0 else float(ex.mean() / vol * np.sqrt(periods_per_year))


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min())


def summary_stats(equity: pd.Series, rf: float = 0.0) -> dict[str, float]:
    r = returns_from_equity(equity)
    return {
        "ann_return": annualized_return(r),
        "ann_vol": annualized_vol(r),
        "sharpe": sharpe(r, rf=rf),
        "max_drawdown": max_drawdown(equity),
    }
