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
        raise NotImplementedError("VolatilityAgent.evaluate will compare realised and implied metrics")


__all__ = ["VolatilityAgent"]
