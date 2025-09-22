"""Execution coordinator for venue-aware order placement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .base import SignalEnvelope


@dataclass(slots=True)
class ExecutionCoordinator:
    """Publishes throttled orders or dry-run actions."""

    dry_run: bool = True

    def execute(self, signals: Iterable[SignalEnvelope]) -> None:
        raise NotImplementedError("ExecutionCoordinator.execute will submit or simulate orders")


__all__ = ["ExecutionCoordinator"]
