"""Exposure guard and kill-switch logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ...data.models import MarketSnapshot
from .base import SignalEnvelope


@dataclass(slots=True)
class RiskGate:
    """Applies hard limits and kill-switch thresholds."""

    max_position_usd: float
    max_drawdown_bps: float

    def filter(self, snapshot: MarketSnapshot, signals: Iterable[SignalEnvelope]) -> List[SignalEnvelope]:
        approved: List[SignalEnvelope] = []
        used_notional = 0.0
        mid_price = snapshot.order_book.mid_price
        for signal in signals:
            if signal.value == 0.0:
                continue
            drawdown_estimate = abs(signal.value) * 10_000.0
            if drawdown_estimate > self.max_drawdown_bps:
                continue
            notional_hint = signal.diagnostics.get("notional_hint", abs(signal.value) * mid_price)
            if notional_hint <= 0.0:
                continue
            if used_notional + notional_hint > self.max_position_usd:
                continue
            approved.append(signal)
            used_notional += notional_hint
        return approved


__all__ = ["RiskGate"]
