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
        raise NotImplementedError("ImbalanceAgent.evaluate will compute depth skews in a later step")


__all__ = ["ImbalanceAgent"]
