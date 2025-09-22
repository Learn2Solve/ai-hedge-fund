"""On-chain flow and funding signals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Iterator

import polars as pl

from ..models import MarketSnapshot
from .base import MarketDataProvider, StreamConfig
from .local_cache import LocalCacheProvider


@dataclass(slots=True)
class OnChainProvider(MarketDataProvider):
    config: StreamConfig
    cache_dir: Path
    name: str = "onchain"
    book_pattern: str | None = None
    trade_pattern: str | None = None
    funding_pattern: str | None = None
    metrics_pattern: str | None = None

    def __post_init__(self) -> None:
        self._base = LocalCacheProvider(
            self.config,
            self.cache_dir,
            name=self.name,
            book_pattern=self.book_pattern,
            trade_pattern=self.trade_pattern,
            funding_pattern=self.funding_pattern,
        )
        metrics_path = self._resolve_metrics_path()
        self._metrics = self._load_metrics(metrics_path) if metrics_path else {}

    def stream(self, *, since: datetime | None = None) -> Iterable[MarketSnapshot]:
        return self._iter_with_metrics(self._base.stream(since=since))

    def latest(self) -> MarketSnapshot:
        base_snapshot = self._base.latest()
        metrics = self._metrics.get(base_snapshot.order_book.timestamp, {})
        combined = dict(base_snapshot.venue_metrics)
        combined.update(metrics)
        return MarketSnapshot(
            symbol=base_snapshot.symbol,
            order_book=base_snapshot.order_book,
            trades=base_snapshot.trades,
            recent_funding=base_snapshot.recent_funding,
            venue_metrics=combined,
        )

    def _iter_with_metrics(self, base_stream: Iterable[MarketSnapshot]) -> Iterator[MarketSnapshot]:
        for snapshot in base_stream:
            timestamp = snapshot.order_book.timestamp
            metrics = self._metrics.get(timestamp, {})
            combined = dict(snapshot.venue_metrics)
            combined.update(metrics)
            yield MarketSnapshot(
                symbol=snapshot.symbol,
                order_book=snapshot.order_book,
                trades=snapshot.trades,
                recent_funding=snapshot.recent_funding,
                venue_metrics=combined,
            )

    def _resolve_metrics_path(self) -> Path | None:
        if self.metrics_pattern:
            candidates = sorted(self.cache_dir.glob(self.metrics_pattern))
            return candidates[-1] if candidates else None
        default = self.cache_dir / f"{self.config.symbol.lower()}_metrics.parquet"
        return default if default.exists() else None

    def _load_metrics(self, path: Path | None) -> Dict[datetime, Dict[str, float]]:
        if path is None or not path.exists():
            return {}
        frame = pl.read_parquet(path)
        metrics: Dict[datetime, Dict[str, float]] = {}
        for row in frame.iter_rows(named=True):
            timestamp = row["timestamp"]
            if not isinstance(timestamp, datetime):
                timestamp = datetime.fromisoformat(str(timestamp))
            metrics[timestamp] = {
                key: float(value)
                for key, value in row.items()
                if key != "timestamp" and value is not None
            }
        return metrics


__all__ = ["OnChainProvider"]
