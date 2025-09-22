"""Signal routing and LangGraph coordination glue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from ...data.models import MarketSnapshot
from .base import SignalAgent, SignalEnvelope


@dataclass(slots=True)
class SignalRouter:
    """Collects agent outputs and forwards approved actions."""

    agents: Sequence[SignalAgent]

    def dispatch(self, snapshot: MarketSnapshot) -> Iterable[SignalEnvelope]:
        raise NotImplementedError("SignalRouter.dispatch will orchestrate agent evaluation and memory writes")


__all__ = ["SignalRouter"]
