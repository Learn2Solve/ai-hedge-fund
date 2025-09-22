from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from src.agents.crypto import ExecutionCoordinator, RiskGate, SignalRouter
from src.agents.crypto.base import SignalAgent, SignalEnvelope
from src.agents.crypto.execution import ExecutionOrder
from src.agents.crypto.router import RouterResult
from src.data.models import FundingEntry, MarketSnapshot, OrderBookLevel, OrderBookSnapshot, Trade
from src.backtesting.crypto_replay import BacktestSummary, CryptoBacktester


def make_snapshot(price: float) -> MarketSnapshot:
    timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    bids = [OrderBookLevel(price=price - 0.5, size=1.0)]
    asks = [OrderBookLevel(price=price + 0.5, size=1.0)]
    book = OrderBookSnapshot(timestamp=timestamp, bids=bids, asks=asks)
    trades = [Trade(timestamp=timestamp, price=price, size=0.1, side="buy")]
    funding = FundingEntry(timestamp=timestamp, rate=0.0)
    return MarketSnapshot(
        symbol="BTCUSDT",
        order_book=book,
        trades=trades,
        recent_funding=funding,
        venue_metrics={},
    )


@dataclass(slots=True)
class StubAgent(SignalAgent):
    name: str = "stub"
    direction: float = 0.4

    def evaluate(self, snapshot: MarketSnapshot) -> SignalEnvelope:
        diagnostics = {"notional_hint": abs(self.direction) * snapshot.order_book.mid_price}
        return SignalEnvelope(self.name, snapshot.symbol, self.direction, 1.0, diagnostics)


def test_crypto_backtester_generates_orders() -> None:
    agent = StubAgent(direction=0.01)
    risk = RiskGate(max_position_usd=5_000.0, max_drawdown_bps=200.0)
    executor = ExecutionCoordinator(max_order_usd=1_000.0)
    router = SignalRouter(agents=[agent], risk_gate=risk, executor=executor)
    backtester = CryptoBacktester(router, starting_cash=10_000.0, fee_bps=2.0, latency_ms=50.0)

    snapshots = [make_snapshot(price=100.0 + i) for i in range(5)]
    summary = backtester.run(snapshots)

    assert isinstance(summary, BacktestSummary)
    assert summary.executed_orders
    assert summary.final_nav != summary.starting_cash
    assert all(isinstance(order, ExecutionOrder) for order in summary.executed_orders)
