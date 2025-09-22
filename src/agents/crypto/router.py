"""Signal routing and LangGraph coordination glue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence

from ...data.models import MarketSnapshot
from .base import SignalAgent, SignalEnvelope
from .execution import ExecutionCoordinator, ExecutionOrder
from .risk_gate import RiskGate

MemoryCallback = Callable[[SignalEnvelope], None]


@dataclass(slots=True)
class SignalRouter:
    """Collects agent outputs and forwards approved actions."""

    agents: Sequence[SignalAgent]
    risk_gate: RiskGate
    executor: ExecutionCoordinator
    memory_callback: MemoryCallback | None = None

    def dispatch(self, snapshot: MarketSnapshot) -> List[ExecutionOrder]:
        envelopes: List[SignalEnvelope] = []
        for agent in self.agents:
            envelope = agent.evaluate(snapshot)
            envelopes.append(envelope)
            if self.memory_callback is not None:
                self.memory_callback(envelope)

        approved = self.risk_gate.filter(snapshot, envelopes)
        return self.executor.execute(snapshot, approved)


__all__ = ["SignalRouter", "MemoryCallback"]
