"""Generate synthetic cache snapshots for notebooks and tests."""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create synthetic cached market data")
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading pair symbol")
    parser.add_argument("--rows", type=int, default=120, help="Number of snapshots to generate")
    parser.add_argument(
        "--output",
        default=".cache/data",
        help="Directory for parquet outputs",
    )
    return parser


def generate_cache(symbol: str, rows: int, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    random.seed(42)
    base_price = 100.0
    timestamps = [datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=i) for i in range(rows)]

    book_rows = []
    trade_rows = []
    funding_rows = []
    metrics_rows = []

    for ts in timestamps:
        drift = random.uniform(-0.05, 0.05)
        base_price = max(10.0, base_price * (1.0 + drift * 0.01))
        bid_price = base_price - 0.5
        ask_price = base_price + 0.5
        book_rows.extend(
            [
                {
                    "timestamp": ts,
                    "side": "bid",
                    "level": 1,
                    "price": bid_price,
                    "size": random.uniform(1.0, 5.0),
                },
                {
                    "timestamp": ts,
                    "side": "bid",
                    "level": 2,
                    "price": bid_price - 0.5,
                    "size": random.uniform(0.5, 3.0),
                },
                {
                    "timestamp": ts,
                    "side": "ask",
                    "level": 1,
                    "price": ask_price,
                    "size": random.uniform(1.0, 5.0),
                },
                {
                    "timestamp": ts,
                    "side": "ask",
                    "level": 2,
                    "price": ask_price + 0.5,
                    "size": random.uniform(0.5, 3.0),
                },
            ]
        )
        trade_rows.append(
            {
                "timestamp": ts,
                "price": base_price + random.uniform(-0.2, 0.2),
                "size": random.uniform(0.05, 0.3),
                "side": random.choice(["buy", "sell"]),
            }
        )
        funding_rows.append(
            {
                "timestamp": ts,
                "rate": random.uniform(-0.0005, 0.0005),
            }
        )
        metrics_rows.append(
            {
                "timestamp": ts,
                "realized_vol": random.uniform(0.3, 0.6),
                "implied_vol_deribit": random.uniform(0.25, 0.55),
                "implied_vol_hyperliquid": random.uniform(0.25, 0.55),
                "spread_bps_binance": random.uniform(1.0, 3.0),
                "spread_bps_okx": random.uniform(1.0, 3.0),
                "spread_bps_hyperliquid": random.uniform(1.0, 3.0),
                "whale_flow_musd": random.uniform(0.0, 5.0),
                "dex_cex_ratio": random.uniform(0.0, 1.0),
            }
        )

    symbol_lower = symbol.lower()
    pl.DataFrame(book_rows).write_parquet(output_dir / f"{symbol_lower}_book.parquet")
    pl.DataFrame(trade_rows).write_parquet(output_dir / f"{symbol_lower}_trade.parquet")
    pl.DataFrame(funding_rows).write_parquet(output_dir / f"{symbol_lower}_funding.parquet")
    pl.DataFrame(metrics_rows).write_parquet(output_dir / f"{symbol_lower}_metrics.parquet")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    generate_cache(args.symbol, args.rows, Path(args.output))
    print(f"Synthetic snapshots written to {args.output}")


if __name__ == "__main__":
    main()
