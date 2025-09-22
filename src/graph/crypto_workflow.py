"""LangGraph workflow for the crypto HFT agents."""

from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import List

from langgraph.graph import END, StateGraph
from typing_extensions import Annotated, TypedDict

from ..agents.crypto import RouterResult, SignalRouter
from ..agents.crypto.base import SignalEnvelope
from ..agents.crypto.execution import ExecutionOrder
from ..data.models import MarketSnapshot


class CryptoState(TypedDict):
    snapshot: MarketSnapshot
    signals: Annotated[List[SignalEnvelope], operator.add]
    orders: Annotated[List[ExecutionOrder], operator.add]


@dataclass(slots=True)
class CryptoWorkflow:
    router: SignalRouter

    def build(self) -> StateGraph:
        graph = StateGraph(CryptoState)
        graph.add_node("evaluate", self._evaluate)
        graph.set_entry_point("evaluate")
        graph.add_edge("evaluate", END)
        return graph

    def _evaluate(self, state: CryptoState) -> CryptoState:
        result: RouterResult = self.router.dispatch(state["snapshot"])
        return {
            "snapshot": state["snapshot"],
            "signals": result.signals,
            "orders": result.orders,
        }


__all__ = ["CryptoWorkflow", "CryptoState"]
