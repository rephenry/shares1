from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class AppConfig:
    base_currency: str
    timezone: str
    benchmark_name: str
    benchmark_ticker: str
    symbol_map: dict[str, str]
    processed_dir: Path
    outputs_dir: Path
    coinspot_api_key: str | None
    coinspot_api_key_header: str
    coinspot_history_url_template: str
    coinspot_timeout_seconds: int


def load_config(path: str) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    coinspot_cfg = cfg.get("coinspot", {}) or {}
    secrets_path = coinspot_cfg.get("secrets_path", "configs/coinspot.private.yml")
    if secrets_path:
        secrets_file = Path(secrets_path)
        if secrets_file.exists():
            with open(secrets_file, "r", encoding="utf-8") as f:
                secrets = yaml.safe_load(f) or {}
            if isinstance(secrets, dict):
                secrets_coinspot = secrets.get("coinspot", secrets)
                if isinstance(secrets_coinspot, dict):
                    coinspot_cfg = {**coinspot_cfg, **secrets_coinspot}

    return AppConfig(
        base_currency=cfg.get("base_currency", "AUD"),
        timezone=cfg.get("timezone", "Australia/Sydney"),
        benchmark_name=cfg["benchmark"]["name"],
        benchmark_ticker=cfg["benchmark"]["ticker"],
        symbol_map=cfg.get("symbol_map", {}),
        processed_dir=Path(cfg["paths"]["processed_dir"]),
        outputs_dir=Path(cfg["paths"]["outputs_dir"]),
        coinspot_api_key=coinspot_cfg.get("api_key"),
        coinspot_api_key_header=coinspot_cfg.get("api_key_header", "key"),
        coinspot_history_url_template=coinspot_cfg.get(
            "history_url_template",
            "https://www.coinspot.com.au/pubapi/v2/market/history?c={symbol}",
        ),
        coinspot_timeout_seconds=int(coinspot_cfg.get("timeout_seconds", 30)),
    )
