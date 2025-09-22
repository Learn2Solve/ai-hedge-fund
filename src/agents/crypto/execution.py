"""Execution coordinator for venue-aware order placement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ...data.models import MarketSnapshot
from .base import SignalEnvelope


@dataclass(frozen=True, slots=True)
class ExecutionOrder:
    """Structured representation of a dry-run order."""

    symbol: str
    side: str
    size: float
    limit_price: float
    source: str


@dataclass(slots=True)
class ExecutionCoordinator:
    """Publishes throttled orders or dry-run actions."""

    dry_run: bool = True
    max_order_usd: float = 1_000.0

    def execute(self, snapshot: MarketSnapshot, signals: Iterable[SignalEnvelope]) -> List[ExecutionOrder]:
        orders: List[ExecutionOrder] = []
        mid_price = snapshot.order_book.mid_price
        if mid_price <= 0.0:
            return orders

        for signal in signals:
            side = "buy" if signal.value > 0.0 else "sell"
            intensity = min(1.0, abs(signal.value))
            notional = self.max_order_usd * intensity
            size = notional / mid_price
            if size == 0.0:
                continue
            orders.append(
                ExecutionOrder(
                    symbol=snapshot.symbol,
                    side=side,
                    size=size,
                    limit_price=mid_price,
                    source=signal.name,
                )
            )
            if not self.dry_run:
                # Live order integration will be implemented once venue APIs are wired.
                ...
        return orders


__all__ = ["ExecutionCoordinator", "ExecutionOrder"]
