"""Volatility and regime classification agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ...data.models import MarketSnapshot
from .base import SignalAgent, SignalEnvelope


@dataclass(slots=True)
class VolatilityAgent(SignalAgent):
    """Assesses realised versus implied volatility regimes."""

    realized_windows: Sequence[int] = (30, 120, 360)
    implied_sources: Sequence[str] = ("deribit", "hyperliquid")

    name: str = "volatility_regime"

    def evaluate(self, snapshot: MarketSnapshot) -> SignalEnvelope:
        realized = snapshot.venue_metrics.get("realized_vol", 0.0)
        implied_values = []
        for source in self.implied_sources:
            key = f"implied_vol_{source}"
            if key in snapshot.venue_metrics:
                implied_values.append(snapshot.venue_metrics[key])
        implied_avg = sum(implied_values) / len(implied_values) if implied_values else realized
        spread = realized - implied_avg
        baseline = implied_avg if implied_avg != 0.0 else 1e-6
        confidence = min(1.0, abs(spread) / baseline)
        notional_hint = abs(spread) * snapshot.order_book.mid_price
        diagnostics = {
            "realized_vol": float(realized),
            "implied_vol": float(implied_avg),
            "spread": float(spread),
            "notional_hint": float(notional_hint),
        }
        return SignalEnvelope(self.name, snapshot.symbol, spread, confidence, diagnostics)


__all__ = ["VolatilityAgent"]
