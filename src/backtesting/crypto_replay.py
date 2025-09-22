"""Event-driven backtester for the crypto agent stack."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ..agents.crypto import RouterResult, SignalRouter
from ..agents.crypto.execution import ExecutionOrder
from ..data.models import MarketSnapshot


@dataclass(frozen=True, slots=True)
class BacktestSummary:
    starting_cash: float
    ending_cash: float
    final_nav: float
    realised_pnl: float
    open_position: float
    executed_orders: List[ExecutionOrder]


class CryptoBacktester:
    """Simple event-driven simulator that honours latency and fees."""

    def __init__(
        self,
        router: SignalRouter,
        *,
        starting_cash: float = 100_000.0,
        fee_bps: float = 1.0,
        latency_ms: float = 150.0,
    ) -> None:
        self.router = router
        self.starting_cash = starting_cash
        self.fee_bps = fee_bps
        self.latency_ms = latency_ms

    def run(self, snapshots: Iterable[MarketSnapshot]) -> BacktestSummary:
        cash = self.starting_cash
        position = 0.0
        executed: List[ExecutionOrder] = []
        last_mid = 0.0

        for snapshot in snapshots:
            last_mid = snapshot.order_book.mid_price
            if last_mid <= 0.0:
                continue
            result: RouterResult = self.router.dispatch(snapshot)
            for order in result.orders:
                effective_price = self._apply_latency(order.limit_price, order.side)
                notional = effective_price * order.size
                fee = notional * (self.fee_bps / 10_000.0)
                if order.side == "buy":
                    cash -= notional + fee
                    position += order.size
                else:
                    cash += notional - fee
                    position -= order.size
                executed.append(order)

        final_nav = cash + position * last_mid
        realised_pnl = final_nav - self.starting_cash
        return BacktestSummary(
            starting_cash=self.starting_cash,
            ending_cash=cash,
            final_nav=final_nav,
            realised_pnl=realised_pnl,
            open_position=position,
            executed_orders=executed,
        )

    def _apply_latency(self, price: float, side: str) -> float:
        slip = price * (self.latency_ms * 1e-6)
        if side == "buy":
            return max(0.0, price + slip)
        return max(0.0, price - slip)


__all__ = ["CryptoBacktester", "BacktestSummary"]
