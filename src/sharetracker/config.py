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


def load_config(path: str) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    return AppConfig(
        base_currency=cfg.get("base_currency", "AUD"),
        timezone=cfg.get("timezone", "Australia/Sydney"),
        benchmark_name=cfg["benchmark"]["name"],
        benchmark_ticker=cfg["benchmark"]["ticker"],
        symbol_map=cfg.get("symbol_map", {}),
        processed_dir=Path(cfg["paths"]["processed_dir"]),
        outputs_dir=Path(cfg["paths"]["outputs_dir"]),
    )
