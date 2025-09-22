"""Dry-run entry point for the crypto HFT pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.agents.crypto import (
    ExecutionCoordinator,
    FlowAgent,
    ImbalanceAgent,
    MomentumAgent,
    RiskGate,
    SignalRouter,
    VolatilityAgent,
)
from src.data.providers import OnChainProvider, StreamConfig
from src.graph.crypto_workflow import CryptoState, CryptoWorkflow
from src.agents.crypto.router import RouterResult
from src.agents.crypto.execution import ExecutionOrder
from src.agents.crypto.base import SignalEnvelope
from scripts.cache_snapshot import generate_cache


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the crypto agent stack on cached snapshots")
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading pair symbol")
    parser.add_argument("--limit", type=int, default=50, help="Number of snapshots to evaluate")
    parser.add_argument("--cache-dir", default=".cache/data", help="Directory containing parquet caches")
    parser.add_argument("--regen", action="store_true", help="Regenerate synthetic cache before running")
    return parser


def ensure_provider(symbol: str, cache_dir: Path, regen: bool) -> OnChainProvider:
    if regen or not (cache_dir / f"{symbol.lower()}_book.parquet").exists():
        generate_cache(symbol, rows=300, output_dir=cache_dir)
    stream_config = StreamConfig(symbol=symbol, depth_levels=2, window_seconds=1)
    return OnChainProvider(stream_config, cache_dir)


def format_order(order: ExecutionOrder) -> str:
    return f"{order.source:<18} {order.side.upper():<4} size={order.size:.6f} @ {order.limit_price:.2f}"


def format_signal(signal: SignalEnvelope) -> str:
    return f"{signal.name:<18} value={signal.value:+.4f} conf={signal.confidence:.2f}"


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    cache_dir = Path(args.cache_dir)

    provider = ensure_provider(args.symbol, cache_dir, args.regen)

    agents = [
        ImbalanceAgent(),
        MomentumAgent(),
        VolatilityAgent(),
        FlowAgent(),
    ]
    risk_gate = RiskGate(max_position_usd=2_000.0, max_drawdown_bps=120.0)
    executor = ExecutionCoordinator(max_order_usd=500.0)
    router = SignalRouter(agents=agents, risk_gate=risk_gate, executor=executor)
    workflow = CryptoWorkflow(router).build().compile()

    snapshot_stream = provider.stream()
    results: list[RouterResult] = []
    for idx, snapshot in enumerate(snapshot_stream):
        if idx >= args.limit:
            break
        state: CryptoState = {
            "snapshot": snapshot,
            "signals": [],
            "orders": [],
        }
        next_state = workflow.invoke(state)
        results.append(RouterResult(signals=next_state["signals"], orders=next_state["orders"]))

    if not results:
        print("No snapshots evaluated. Check cache generation.")
        return

    print(f"Evaluated {len(results)} snapshots for {args.symbol} (dry-run)")
    latest = results[-1]
    print("\nSignals (latest snapshot):")
    for signal in latest.signals:
        print("  " + format_signal(signal))
    print("\nOrders (latest snapshot):")
    if latest.orders:
        for order in latest.orders:
            print("  " + format_order(order))
    else:
        print("  (risk gate blocked orders)")


if __name__ == "__main__":
    main()
