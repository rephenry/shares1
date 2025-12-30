from __future__ import annotations

import numpy as np
import pandas as pd


def beta_alpha(port_r: pd.Series, bench_r: pd.Series, rf_daily: float = 0.0) -> dict[str, float]:
    df = pd.concat([port_r, bench_r], axis=1).dropna()
    if df.shape[0] < 5:
        return {"beta": 0.0, "alpha_daily": 0.0}

    y = df.iloc[:, 0] - rf_daily
    x = df.iloc[:, 1] - rf_daily

    cov = float(np.cov(x, y, ddof=1)[0, 1])
    var = float(np.var(x, ddof=1))
    beta = cov / var if var != 0 else 0.0
    alpha = float(y.mean() - beta * x.mean())
    return {"beta": beta, "alpha_daily": alpha}
