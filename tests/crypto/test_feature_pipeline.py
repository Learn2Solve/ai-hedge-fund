from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import polars as pl

import sys

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.data.models import (
    FundingEntry,
    MarketSnapshot,
    OrderBookLevel,
    OrderBookSnapshot,
    Trade,
)
from src.data.pipelines import FeaturePipeline, PipelineConfig
from src.data.providers import MarketDataProvider, StreamConfig


@dataclass(slots=True)
class StubProvider(MarketDataProvider):
    snapshots: list[MarketSnapshot]
    name: str = "stub"

    def stream(self, *, since: datetime | None = None) -> Iterable[MarketSnapshot]:
        for snapshot in self.snapshots:
            if since and snapshot.order_book.timestamp <= since:
                continue
            yield snapshot

    def latest(self) -> MarketSnapshot:
        return self.snapshots[-1]


def make_snapshot(price: float, *, trade_count: int) -> MarketSnapshot:
    timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    bids = [OrderBookLevel(price=price - 0.5, size=1.0)]
    asks = [OrderBookLevel(price=price + 0.5, size=1.2)]
    snapshot = OrderBookSnapshot(timestamp=timestamp, bids=bids, asks=asks)
    trades = [
        Trade(timestamp=timestamp, price=price, size=0.1, side="buy")
        for _ in range(trade_count)
    ]
    funding = FundingEntry(timestamp=timestamp, rate=0.0001)
    return MarketSnapshot(
        symbol="BTCUSDT",
        order_book=snapshot,
        trades=trades,
        recent_funding=funding,
        venue_metrics={"binance_spread_bps": 5.0},
    )


def test_snapshots_to_frame() -> None:
    provider = StubProvider([])
    pipeline = FeaturePipeline(
        provider,
        PipelineConfig(stream=StreamConfig(symbol="BTCUSDT", depth_levels=10, window_seconds=60)),
    )
    frame = pipeline.snapshots_to_frame([])
    assert frame.shape == (0, 7)
    assert frame.schema["symbol"] == pl.String

    snapshot = make_snapshot(100.0, trade_count=3)
    frame = pipeline.snapshots_to_frame([snapshot])
    assert frame.shape == (1, 7)
    row = frame.to_dicts()[0]
    assert row["symbol"] == "BTCUSDT"
    assert row["mid_price"] == 100.0
    assert row["trade_count"] == 3


def test_collect_respects_limit() -> None:
    snapshots = [make_snapshot(100.0 + i, trade_count=1) for i in range(5)]
    provider = StubProvider(snapshots)
    pipeline = FeaturePipeline(
        provider,
        PipelineConfig(stream=StreamConfig(symbol="BTCUSDT", depth_levels=10, window_seconds=60)),
    )
    collected = pipeline.collect(limit=2)
    assert len(collected) == 2
    assert collected[0].order_book.mid_price == 100.0
    assert collected[1].order_book.mid_price == 101.0
