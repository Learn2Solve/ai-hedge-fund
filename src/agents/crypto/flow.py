"""Cross-venue flow intelligence agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ...data.models import MarketSnapshot
from .base import SignalAgent, SignalEnvelope


@dataclass(slots=True)
class FlowAgent(SignalAgent):
    """Flags abnormal spreads, whale activity, and CEX↔DEX transfers."""

    venues: Sequence[str] = ("binance", "okx", "hyperliquid", "jupiter")

    name: str = "flow_intelligence"

    def evaluate(self, snapshot: MarketSnapshot) -> SignalEnvelope:
        spreads = []
        for venue in self.venues:
            key = f"spread_bps_{venue}"
            if key in snapshot.venue_metrics:
                spreads.append(snapshot.venue_metrics[key])
        avg_spread_bps = sum(spreads) / len(spreads) if spreads else 0.0
        whale_flow = snapshot.venue_metrics.get("whale_flow_musd", 0.0)
        dex_cex = snapshot.venue_metrics.get("dex_cex_ratio", 0.0)

        normalized_spread = avg_spread_bps / 10_000.0
        value = normalized_spread + (whale_flow / 100.0) + (dex_cex * 0.1)
        confidence = min(1.0, abs(value) * 20.0)
        notional_hint = abs(value) * snapshot.order_book.mid_price
        diagnostics = {
            "avg_spread_bps": float(avg_spread_bps),
            "whale_flow_musd": float(whale_flow),
            "dex_cex_ratio": float(dex_cex),
            "notional_hint": float(notional_hint),
        }
        return SignalEnvelope(self.name, snapshot.symbol, value, confidence, diagnostics)


__all__ = ["FlowAgent"]
