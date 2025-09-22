"""Exposure guard and kill-switch logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .base import SignalEnvelope


@dataclass(slots=True)
class RiskGate:
    """Applies hard limits and kill-switch thresholds."""

    max_position_usd: float
    max_drawdown_bps: float

    def filter(self, signals: Iterable[SignalEnvelope]) -> Iterable[SignalEnvelope]:
        raise NotImplementedError("RiskGate.filter will enforce exposure constraints and circuit breakers")


__all__ = ["RiskGate"]
