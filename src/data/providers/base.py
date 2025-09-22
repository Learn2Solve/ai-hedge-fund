"""Interfaces for market-data providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from ..models import MarketSnapshot


@dataclass(frozen=True, slots=True)
class StreamConfig:
    symbol: str
    depth_levels: int
    window_seconds: int


class MarketDataProvider(ABC):
    """Thin wrapper over venue-specific APIs."""

    name: str

    @abstractmethod
    def stream(self, *, since: datetime | None = None) -> Iterable[MarketSnapshot]:  # pragma: no cover - abstract
        """Yield market snapshots for the configured symbol."""

    @abstractmethod
    def latest(self) -> MarketSnapshot:  # pragma: no cover - abstract
        """Return a single snapshot for synchronous workflows."""
