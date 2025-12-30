from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px


def save_equity_curve_chart(df: pd.DataFrame, out_html: Path, title: str) -> None:
    fig = px.line(df, x=df.index, y=df.columns, title=title)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_html))


def save_drawdown_chart(equity: pd.Series, out_html: Path, title: str) -> None:
    peak = equity.cummax()
    dd = equity / peak - 1.0
    fig = px.area(dd, title=title)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_html))
