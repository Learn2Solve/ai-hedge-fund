from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

import polars as pl

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.data.providers import LocalCacheProvider, StreamConfig


def write_frames(tmp_path):
    timestamps = [datetime(2024, 1, 1, tzinfo=timezone.utc)] * 4
    book = pl.DataFrame(
        {
            "timestamp": timestamps,
            "side": ["bid", "bid", "ask", "ask"],
            "level": [1, 2, 1, 2],
            "price": [99.5, 99.4, 100.5, 100.6],
            "size": [1.0, 0.5, 1.2, 0.4],
        }
    )
    book.write_parquet(tmp_path / "btcusdt_book.parquet")

    trades = pl.DataFrame(
        {
            "timestamp": [timestamps[0], timestamps[0]],
            "price": [100.0, 100.1],
            "size": [0.1, 0.2],
            "side": ["buy", "sell"],
        }
    )
    trades.write_parquet(tmp_path / "btcusdt_trade.parquet")

    funding = pl.DataFrame(
        {
            "timestamp": [timestamps[0]],
            "rate": [0.0003],
        }
    )
    funding.write_parquet(tmp_path / "btcusdt_funding.parquet")


def test_local_cache_provider_stream(tmp_path) -> None:
    write_frames(tmp_path)
    provider = LocalCacheProvider(
        StreamConfig(symbol="BTCUSDT", depth_levels=2, window_seconds=60),
        cache_dir=tmp_path,
    )

    snapshots = list(provider.stream())
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.symbol == "BTCUSDT"
    assert snapshot.order_book.best_bid == 99.5
    assert snapshot.order_book.best_ask == 100.5
    assert snapshot.trades[0].price == 100.0
    assert snapshot.recent_funding and snapshot.recent_funding.rate == 0.0003

    latest = provider.latest()
    assert latest.order_book.mid_price == 100.0


def test_local_cache_provider_wide_format(tmp_path) -> None:
    timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    book = pl.DataFrame(
        {
            "datetime": [timestamp, timestamp],
            "side": ["ASK", "BID"],
            "price_1": [101.0, 100.8],
            "size_1": [2.5, 3.1],
            "price_2": [101.2, 100.6],
            "size_2": [1.0, 1.4],
        }
    )
    book.write_parquet(tmp_path / "pair_l2_book.parquet")

    trades = pl.DataFrame(
        {
            "datetime": [timestamp, timestamp],
            "price": [101.0, 100.9],
            "size": [0.2, 0.15],
            "taker_side": ["BUY", "SELL"],
        }
    )
    trades.write_parquet(tmp_path / "pair_trade.parquet")

    provider = LocalCacheProvider(
        StreamConfig(symbol="PAIR", depth_levels=2, window_seconds=60),
        cache_dir=tmp_path,
        book_pattern="*_l2_book.parquet",
        trade_pattern="*_trade.parquet",
    )

    snapshot = next(iter(provider.stream()))
    assert snapshot.order_book.best_ask == 101.0
    assert snapshot.order_book.best_bid == 100.8
    assert snapshot.trades[0].side == "buy"
    assert snapshot.trades[0].price == 101.0
