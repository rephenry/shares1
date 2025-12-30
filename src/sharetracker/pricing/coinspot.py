from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import urllib.error
import urllib.request

import pandas as pd


def _extract_rows(payload: object) -> list[dict]:
    if isinstance(payload, dict):
        for key in ("prices", "data", "history", "result"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return rows
        return []
    if isinstance(payload, list):
        return payload
    return []


def _extract_timestamp(row: dict) -> pd.Timestamp | None:
    for key in ("date", "timestamp", "time", "datetime", "created", "created_at"):
        if key not in row:
            continue
        raw = row.get(key)
        if raw is None:
            continue
        if isinstance(raw, (int, float)):
            unit = "ms" if raw > 1_000_000_000_000 else "s"
            ts = pd.to_datetime(raw, unit=unit, utc=True)
        else:
            ts = pd.to_datetime(str(raw), utc=True, errors="coerce")
        if ts is pd.NaT:
            continue
        return ts.tz_convert(None)
    return None


def _extract_price_value(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("last", "price", "close", "bid", "ask", "rate"):
            if key in value and value[key] is not None:
                try:
                    return float(value[key])
                except (TypeError, ValueError):
                    return None
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _extract_price(row: dict) -> float | None:
    for key in ("close", "price", "last", "rate"):
        if key in row and row[key] is not None:
            return _extract_price_value(row[key])
    return None


def _payload_to_frame(payload: object) -> pd.DataFrame:
    rows = _extract_rows(payload)
    if not rows:
        return pd.DataFrame()

    data = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        ts = _extract_timestamp(row)
        price = _extract_price(row)
        if ts is None or price is None:
            continue
        data.append({"dt": ts, "close": price})

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data).drop_duplicates("dt").set_index("dt").sort_index()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df


def _payload_latest_to_frame(payload: object, symbol: str, start: str, end: str) -> pd.DataFrame:
    if not isinstance(payload, dict):
        return pd.DataFrame()
    prices = payload.get("prices")
    if not isinstance(prices, dict):
        return pd.DataFrame()

    key = symbol.lower()
    value = prices.get(key)
    if value is None:
        value = prices.get(symbol.upper()) or prices.get(symbol.lower())
    if value is None:
        return pd.DataFrame()

    price = _extract_price_value(value)
    if price is None:
        return pd.DataFrame()

    idx = pd.bdate_range(start=start, end=end)
    if len(idx) == 0:
        idx = pd.DatetimeIndex([pd.to_datetime(start)])
    df = pd.DataFrame({"close": [price] * len(idx)}, index=idx)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df


@dataclass
class CoinspotPriceCache:
    cache_dir: Path
    history_url_template: str
    latest_url: str | None = None
    api_key: str | None = None
    api_key_header: str = "key"
    timeout_seconds: int = 30

    def cache_path(self, ticker: str) -> Path:
        safe = ticker.replace("^", "_").replace("/", "_")
        return self.cache_dir / f"prices_coinspot_{safe}.parquet"

    def _coin_symbol(self, ticker: str) -> str:
        return ticker.split("-", 1)[0].upper()

    def _fetch_history(self, ticker: str) -> pd.DataFrame:
        coin = self._coin_symbol(ticker)
        url = self.history_url_template.format(symbol=coin, coin=coin, ticker=ticker)
        req = urllib.request.Request(url)
        if self.api_key:
            req.add_header(self.api_key_header, self.api_key)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                payload = json.load(resp)
        except urllib.error.HTTPError as exc:
            print(f"Warning: CoinSpot history fetch failed for {ticker} ({exc.code})")
            return pd.DataFrame()
        return _payload_to_frame(payload)

    def _fetch_latest(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        if not self.latest_url:
            return pd.DataFrame()
        req = urllib.request.Request(self.latest_url)
        if self.api_key:
            req.add_header(self.api_key_header, self.api_key)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                payload = json.load(resp)
        except urllib.error.HTTPError as exc:
            print(f"Warning: CoinSpot latest fetch failed ({exc.code})")
            return pd.DataFrame()
        return _payload_latest_to_frame(payload, self._coin_symbol(ticker), start, end)

    def load_or_fetch(self, ticker: str, start: str, end: str) -> pd.Series:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        p = self.cache_path(ticker)

        if p.exists():
            df = pd.read_parquet(p)
        else:
            df = pd.DataFrame()

        need_fetch = df.empty or df.index.min() > pd.to_datetime(start) or df.index.max() < pd.to_datetime(end)

        if need_fetch:
            if self.latest_url:
                df = self._fetch_latest(ticker, start, end)
            else:
                df = self._fetch_history(ticker)
            if df.empty:
                print(f"Warning: No CoinSpot data for ticker: {ticker}")
                return pd.Series(name="close", dtype=float)
            df.to_parquet(p)

        s = df["close"].copy()
        s.index = pd.to_datetime(s.index).tz_localize(None)
        s = s.loc[(s.index >= pd.to_datetime(start)) & (s.index <= pd.to_datetime(end))]
        return s
