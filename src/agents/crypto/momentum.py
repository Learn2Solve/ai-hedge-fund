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
        raise NotImplementedError("MomentumAgent.evaluate will track short-horizon z-scores")


__all__ = ["MomentumAgent"]
