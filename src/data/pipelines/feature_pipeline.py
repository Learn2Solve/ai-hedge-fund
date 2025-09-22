"""Feature pipeline scaffolding for crypto order-book data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import polars as pl

from ..models import MarketSnapshot
from ..providers import MarketDataProvider, StreamConfig


@dataclass(slots=True)
class PipelineConfig:
    """Simple configuration for assembling features."""

    stream: StreamConfig
    cache_dir: Path = Path(".cache/data")
    levels: Sequence[int] = (1, 3, 5, 10)


class FeaturePipeline:
    """Collects snapshots and materialises feature tables."""

    def __init__(self, provider: MarketDataProvider, config: PipelineConfig) -> None:
        self.provider = provider
        self.config = config

    def collect(self, *, limit: int) -> list[MarketSnapshot]:
        snapshots: list[MarketSnapshot] = []
        for snapshot in self.provider.stream():
            snapshots.append(snapshot)
            if len(snapshots) >= limit:
                break
        return snapshots

    def snapshots_to_frame(self, snapshots: Iterable[MarketSnapshot]) -> pl.DataFrame:
        rows = []
        for snap in snapshots:
            mid = snap.order_book.mid_price
            rows.append(
                {
                    "timestamp": snap.order_book.timestamp,
                    "symbol": snap.symbol,
                    "mid_price": mid,
                    "best_bid": snap.order_book.best_bid,
                    "best_ask": snap.order_book.best_ask,
                    "trade_count": len(snap.trades),
                    "funding_rate": snap.recent_funding.rate if snap.recent_funding else 0.0,
                }
            )
        if not rows:
            return pl.DataFrame(
                {
                    "timestamp": pl.Series([], dtype=pl.Datetime),
                    "symbol": pl.Series([], dtype=pl.String),
                    "mid_price": pl.Series([], dtype=pl.Float64),
                    "best_bid": pl.Series([], dtype=pl.Float64),
                    "best_ask": pl.Series([], dtype=pl.Float64),
                    "trade_count": pl.Series([], dtype=pl.Int64),
                    "funding_rate": pl.Series([], dtype=pl.Float64),
                }
            )
        return pl.DataFrame(rows)


__all__ = ["PipelineConfig", "FeaturePipeline"]
