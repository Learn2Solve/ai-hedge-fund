from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.agents.crypto import (
    ExecutionCoordinator,
    FlowAgent,
    ImbalanceAgent,
    MomentumAgent,
    RiskGate,
    SignalRouter,
    VolatilityAgent,
)
from src.data.models import (
    FundingEntry,
    MarketSnapshot,
    OrderBookLevel,
    OrderBookSnapshot,
    Trade,
)


def make_snapshot(*, price: float = 100.0) -> MarketSnapshot:
    timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    bids = [
        OrderBookLevel(price=price - 0.5, size=2.0),
        OrderBookLevel(price=price - 1.0, size=1.8),
    ]
    asks = [
        OrderBookLevel(price=price + 0.5, size=1.0),
        OrderBookLevel(price=price + 1.0, size=0.8),
    ]
    book = OrderBookSnapshot(timestamp=timestamp, bids=bids, asks=asks)
    trades = [
        Trade(timestamp=timestamp, price=price - 0.2, size=0.1, side="sell"),
        Trade(timestamp=timestamp, price=price - 0.1, size=0.1, side="sell"),
        Trade(timestamp=timestamp, price=price, size=0.2, side="buy"),
        Trade(timestamp=timestamp, price=price + 0.2, size=0.15, side="buy"),
    ]
    funding = FundingEntry(timestamp=timestamp, rate=0.0005)
    metrics = {
        "realized_vol": 0.45,
        "implied_vol_deribit": 0.40,
        "implied_vol_hyperliquid": 0.38,
        "spread_bps_binance": 2.0,
        "spread_bps_okx": 1.5,
        "spread_bps_hyperliquid": 1.8,
        "whale_flow_musd": 3.0,
        "dex_cex_ratio": 0.3,
    }
    return MarketSnapshot(
        symbol="BTCUSDT",
        order_book=book,
        trades=trades,
        recent_funding=funding,
        venue_metrics=metrics,
    )


def test_imbalance_agent() -> None:
    snapshot = make_snapshot()
    agent = ImbalanceAgent(levels=(1, 2))
    envelope = agent.evaluate(snapshot)
    assert envelope.name == "imbalance"
    assert envelope.value > 0
    assert envelope.diagnostics["levels_covered"] == 2.0


def test_momentum_agent() -> None:
    snapshot = make_snapshot(price=101.0)
    agent = MomentumAgent(windows=(2, 4))
    envelope = agent.evaluate(snapshot)
    assert envelope.value != 0.0
    assert envelope.diagnostics["funding_rate"] == 0.0005


def test_volatility_agent() -> None:
    snapshot = make_snapshot()
    agent = VolatilityAgent()
    envelope = agent.evaluate(snapshot)
    assert envelope.value > 0.0
    assert "spread" in envelope.diagnostics


def test_flow_agent() -> None:
    snapshot = make_snapshot()
    agent = FlowAgent()
    envelope = agent.evaluate(snapshot)
    assert envelope.diagnostics["avg_spread_bps"] > 0.0


def test_router_and_risk_and_execution() -> None:
    snapshot = make_snapshot()
    agents = [ImbalanceAgent(levels=(1, 2)), MomentumAgent(windows=(2, 4))]
    risk = RiskGate(max_position_usd=500.0, max_drawdown_bps=80.0)
    executor = ExecutionCoordinator(max_order_usd=250.0)
    router = SignalRouter(agents=agents, risk_gate=risk, executor=executor)
    orders = router.dispatch(snapshot)
    assert orders
    assert all(order.symbol == "BTCUSDT" for order in orders)
