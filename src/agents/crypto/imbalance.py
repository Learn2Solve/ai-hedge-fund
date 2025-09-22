"""Order-book imbalance signal."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ...data.models import MarketSnapshot
from .base import SignalAgent, SignalEnvelope


@dataclass(slots=True)
class ImbalanceAgent(SignalAgent):
    """Computes queue-depth skews across book levels."""

    levels: Sequence[int] = (1, 3, 5, 10)

    name: str = "imbalance"

    def evaluate(self, snapshot: MarketSnapshot) -> SignalEnvelope:
        bids = snapshot.order_book.bids
        asks = snapshot.order_book.asks
        usable = [lvl for lvl in self.levels if lvl <= len(bids) and lvl <= len(asks)]
        if not usable:
            diagnostics = {"levels_covered": 0.0, "avg_skew": 0.0, "max_skew": 0.0, "notional_hint": 0.0}
            return SignalEnvelope(self.name, snapshot.symbol, 0.0, 0.0, diagnostics)

        skews = []
        for depth in usable:
            bid_size = bids[depth - 1].size
            ask_size = asks[depth - 1].size
            total = bid_size + ask_size
            skew = 0.0 if total == 0.0 else (bid_size - ask_size) / total
            skews.append(skew)

        value = sum(skews) / len(skews)
        confidence = min(1.0, abs(value))
        notional_hint = abs(value) * snapshot.order_book.mid_price
        diagnostics = {
            "levels_covered": float(len(usable)),
            "avg_skew": float(value),
            "max_skew": float(max(skews, key=abs)),
            "notional_hint": float(notional_hint),
        }
        return SignalEnvelope(self.name, snapshot.symbol, value, confidence, diagnostics)


__all__ = ["ImbalanceAgent"]
