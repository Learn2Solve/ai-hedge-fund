"""Shared types for crypto signal agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Protocol

from ...data.models import MarketSnapshot


@dataclass(frozen=True)
class SignalEnvelope:
    """Uniform container for agent outputs."""

    name: str
    value: float
    confidence: float
    diagnostics: Dict[str, float]


class SignalAgent(Protocol):
    """Minimal interface every crypto agent implements."""

    name: str

    def evaluate(self, snapshot: MarketSnapshot) -> SignalEnvelope:
        ...
