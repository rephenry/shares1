from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import yfinance as yf


@dataclass
class PriceCache:
    cache_dir: Path

    def cache_path(self, ticker: str) -> Path:
        safe = ticker.replace("^", "_").replace("/", "_")
        return self.cache_dir / f"prices_{safe}.parquet"

    def load_or_fetch(self, ticker: str, start: str, end: str) -> pd.Series:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        p = self.cache_path(ticker)

        if p.exists():
            df = pd.read_parquet(p)
        else:
            df = pd.DataFrame()

        need_fetch = df.empty or df.index.min() > pd.to_datetime(start) or df.index.max() < pd.to_datetime(end)

        if need_fetch:
            hist = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
            if hist.empty:
                raise ValueError(f"No Yahoo Finance data for ticker: {ticker}")
            px = hist["Close"].rename("close").to_frame()
            px.index = pd.to_datetime(px.index).tz_localize(None)
            df = px
            df.to_parquet(p)

        s = df["close"].copy()
        s.index = pd.to_datetime(s.index).tz_localize(None)
        s = s.loc[(s.index >= pd.to_datetime(start)) & (s.index <= pd.to_datetime(end))]
        return s
