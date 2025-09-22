"""Micro-momentum signal agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ...data.models import MarketSnapshot
from .base import SignalAgent, SignalEnvelope


@dataclass(slots=True)
class MomentumAgent(SignalAgent):
    """Evaluates short-horizon return drifts with funding input."""

    windows: Sequence[int] = (5, 15, 60)

    name: str = "micro_momentum"

    def evaluate(self, snapshot: MarketSnapshot) -> SignalEnvelope:
        prices = [trade.price for trade in snapshot.trades]
        if not prices:
            diagnostics = {"windows": 0.0, "avg_return": 0.0, "funding_rate": 0.0, "notional_hint": 0.0}
            return SignalEnvelope(self.name, snapshot.symbol, 0.0, 0.0, diagnostics)

        returns = []
        for window in self.windows:
            if window <= 1 or window > len(prices):
                continue
            start = prices[-window]
            end = prices[-1]
            if start == 0.0:
                continue
            returns.append((end - start) / start)

        value = sum(returns) / len(returns) if returns else 0.0
        funding_rate = snapshot.recent_funding.rate if snapshot.recent_funding else 0.0
        adjusted = value + funding_rate
        confidence = min(1.0, abs(adjusted) * 50.0)
        notional_hint = abs(adjusted) * snapshot.order_book.mid_price
        diagnostics = {
            "windows": float(len(returns)),
            "avg_return": float(value),
            "funding_rate": float(funding_rate),
            "notional_hint": float(notional_hint),
        }
        return SignalEnvelope(self.name, snapshot.symbol, adjusted, confidence, diagnostics)


__all__ = ["MomentumAgent"]
