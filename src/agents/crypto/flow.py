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
        raise NotImplementedError("FlowAgent.evaluate will correlate venue flows")


__all__ = ["FlowAgent"]
