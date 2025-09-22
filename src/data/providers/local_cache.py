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
    book_pattern: str | None = None
    trade_pattern: str | None = None
    funding_pattern: str | None = None

    def __post_init__(self) -> None:
        self._book_path = self._resolve_path("book", pattern=self.book_pattern)
        self._trade_path = self._resolve_path("trade", pattern=self.trade_pattern)
        self._funding_path = self._resolve_path("funding", pattern=self.funding_pattern, optional=True)

        self._book_frame = pl.read_parquet(self._book_path)
        self._trade_frame = pl.read_parquet(self._trade_path)
        self._funding_frame = pl.read_parquet(self._funding_path) if self._funding_path else None

        self._book_timestamp_col = self._detect_timestamp_column(self._book_frame)
        self._trade_timestamp_col = self._detect_timestamp_column(self._trade_frame)
        self._funding_timestamp_col = (
            self._detect_timestamp_column(self._funding_frame) if self._funding_frame is not None else None
        )

    def _resolve_path(self, suffix: str, *, pattern: str | None = None, optional: bool = False) -> Path | None:
        if pattern:
            candidates = sorted(self.cache_dir.glob(pattern))
        else:
            symbol = self.config.symbol.lower()
            default = self.cache_dir / f"{symbol}_{suffix}.parquet"
            candidates = [default] if default.exists() else []

        if candidates:
            return candidates[-1]
        if optional:
            return None
        expected = pattern or f"{self.config.symbol.lower()}_{suffix}.parquet"
        raise FileNotFoundError(f"Missing cache file matching {expected} in {self.cache_dir}")

    @staticmethod
    def _detect_timestamp_column(frame: pl.DataFrame | None) -> str:
        if frame is None:
            return "timestamp"
        if "timestamp" in frame.columns:
            return "timestamp"
        if "datetime" in frame.columns:
            return "datetime"
        raise ValueError("Dataframe must contain either 'timestamp' or 'datetime'")

    def stream(self, *, since: datetime | None = None) -> Iterable[MarketSnapshot]:
        return self._iter_snapshots(since=since)

    def latest(self) -> MarketSnapshot:
        return next(reversed(list(self._iter_snapshots())))

    def _iter_snapshots(self, *, since: datetime | None = None) -> Iterator[MarketSnapshot]:
        book = self._book_frame
        trades = self._trade_frame
        funding = self._funding_frame

        grouped = book.group_by([self._book_timestamp_col], maintain_order=True)
        for keys, group in grouped:
            timestamp = keys[0] if isinstance(keys, tuple) else keys
            ts = _to_datetime(timestamp)
            if since and ts <= since:
                continue
            bids = _collect_side(group, "bid", self.config.depth_levels)
            asks = _collect_side(group, "ask", self.config.depth_levels)
            trade_rows = trades.filter(pl.col(self._trade_timestamp_col) == timestamp)
            trade_entries = [
                Trade(
                    timestamp=_to_datetime(row[self._trade_timestamp_col]),
                    price=float(row["price"]),
                    size=float(row["size"]),
                    side=str(row.get("side") or row.get("taker_side", "")).lower() or "unknown",
                )
                for row in trade_rows.iter_rows(named=True)
            ]
            funding_entry = None
            if funding is not None:
                col = self._funding_timestamp_col or self._book_timestamp_col
                f_rows = funding.filter(pl.col(col) == timestamp)
                if f_rows.height > 0:
                    f_row = f_rows.row(0, named=True)
                    funding_entry = FundingEntry(
                        timestamp=_to_datetime(f_row[col]),
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
    subset = frame.filter(pl.col("side").str.to_lowercase() == side.lower())
    if "level" in subset.columns and "price" in subset.columns:
        subset = subset.sort("level")
        levels: list[OrderBookLevel] = []
        for row in subset.iter_rows(named=True):
            levels.append(
                OrderBookLevel(price=float(row["price"]), size=float(row["size"]))
            )
            if len(levels) >= depth:
                break
        return levels

    if "price_1" in frame.columns:
        side_row = subset.head(1)
        if side_row.height == 0:
            return []
        row = side_row.row(0, named=True)
        levels = []
        for idx in range(1, depth + 1):
            price_key = f"price_{idx}"
            size_key = f"size_{idx}"
            price = row.get(price_key)
            size = row.get(size_key)
            if price is None or size is None:
                break
            levels.append(OrderBookLevel(price=float(price), size=float(size)))
        return levels

    raise ValueError("Unsupported order-book schema for LocalCacheProvider")


def _to_datetime(value: datetime | int | float | str) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    return datetime.fromisoformat(str(value))


__all__ = ["LocalCacheProvider"]
