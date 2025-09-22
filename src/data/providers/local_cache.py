"""Local cache-backed provider reading parquet snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator

import polars as pl

from ..models import (
    FundingEntry,
    MarketSnapshot,
    OrderBookLevel,
    OrderBookSnapshot,
    Trade,
)
from .base import MarketDataProvider, StreamConfig


@dataclass(slots=True)
class LocalCacheProvider(MarketDataProvider):
    """Reads pre-recorded order book and trade data from parquet files."""

    config: StreamConfig
    cache_dir: Path
    name: str = "local_cache"

    def __post_init__(self) -> None:
        self._book_path = self._resolve_path("book")
        self._trade_path = self._resolve_path("trade")
        self._funding_path = self._resolve_path("funding", optional=True)
        self._book_frame = pl.read_parquet(self._book_path)
        self._trade_frame = pl.read_parquet(self._trade_path)
        self._funding_frame = pl.read_parquet(self._funding_path) if self._funding_path else None

    def _resolve_path(self, suffix: str, *, optional: bool = False) -> Path | None:
        symbol = self.config.symbol.lower()
        pattern = f"{symbol}_{suffix}.parquet"
        path = self.cache_dir / pattern
        if path.exists():
            return path
        if optional:
            return None
        raise FileNotFoundError(f"Missing cache file {pattern} in {self.cache_dir}")

    def stream(self, *, since: datetime | None = None) -> Iterable[MarketSnapshot]:
        return self._iter_snapshots(since=since)

    def latest(self) -> MarketSnapshot:
        return next(reversed(list(self._iter_snapshots())))

    def _iter_snapshots(self, *, since: datetime | None = None) -> Iterator[MarketSnapshot]:
        book = self._book_frame
        trades = self._trade_frame
        funding = self._funding_frame

        grouped = book.group_by(["timestamp"], maintain_order=True)
        for keys, group in grouped:
            timestamp = keys[0] if isinstance(keys, tuple) else keys
            ts = _to_datetime(timestamp)
            if since and ts <= since:
                continue
            bids = _collect_side(group, "bid", self.config.depth_levels)
            asks = _collect_side(group, "ask", self.config.depth_levels)
            trade_rows = trades.filter(pl.col("timestamp") == timestamp)
            trade_entries = [
                Trade(
                    timestamp=_to_datetime(row["timestamp"]),
                    price=float(row["price"]),
                    size=float(row["size"]),
                    side=str(row["side"]),
                )
                for row in trade_rows.iter_rows(named=True)
            ]
            funding_entry = None
            if funding is not None:
                f_rows = funding.filter(pl.col("timestamp") == timestamp)
                if f_rows.height > 0:
                    f_row = f_rows.row(0, named=True)
                    funding_entry = FundingEntry(
                        timestamp=_to_datetime(f_row["timestamp"]),
                        rate=float(f_row["rate"]),
                    )
            yield MarketSnapshot(
                symbol=self.config.symbol,
                order_book=OrderBookSnapshot(timestamp=ts, bids=bids, asks=asks),
                trades=trade_entries,
                recent_funding=funding_entry,
                venue_metrics={},
            )


def _collect_side(frame: pl.DataFrame, side: str, depth: int) -> list[OrderBookLevel]:
    subset = frame.filter(pl.col("side") == side).sort("level")
    levels = []
    for row in subset.iter_rows(named=True):
        levels.append(
            OrderBookLevel(price=float(row["price"]), size=float(row["size"]))
        )
        if len(levels) >= depth:
            break
    return levels


def _to_datetime(value: datetime | int | float | str) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    return datetime.fromisoformat(str(value))


__all__ = ["LocalCacheProvider"]
