"""Signal routing and LangGraph coordination glue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Sequence

from ...data.models import MarketSnapshot
from .base import SignalAgent, SignalEnvelope
from .execution import ExecutionCoordinator, ExecutionOrder
from .risk_gate import RiskGate

MemoryCallback = Callable[[SignalEnvelope], None]


@dataclass(frozen=True, slots=True)
class RouterResult:
    signals: List[SignalEnvelope]
    orders: List[ExecutionOrder]


@dataclass(slots=True)
class SignalRouter:
    """Collects agent outputs and forwards approved actions."""

    agents: Sequence[SignalAgent]
    risk_gate: RiskGate
    executor: ExecutionCoordinator
    memory_callback: MemoryCallback | None = None

    def dispatch(self, snapshot: MarketSnapshot) -> RouterResult:
        envelopes: List[SignalEnvelope] = []
        for agent in self.agents:
            envelope = agent.evaluate(snapshot)
            envelopes.append(envelope)
            if self.memory_callback is not None:
                self.memory_callback(envelope)

        approved = self.risk_gate.filter(snapshot, envelopes)
        orders = self.executor.execute(snapshot, approved)
        return RouterResult(signals=envelopes, orders=orders)


__all__ = ["SignalRouter", "MemoryCallback", "RouterResult"]
