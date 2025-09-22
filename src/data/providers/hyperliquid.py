"""Hyperliquid market data adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from ..models import MarketSnapshot
from .base import MarketDataProvider, StreamConfig


@dataclass(slots=True)
class HyperliquidProvider(MarketDataProvider):
    config: StreamConfig
    name: str = "hyperliquid"

    def stream(self, *, since: datetime | None = None) -> Iterable[MarketSnapshot]:
        raise NotImplementedError("HyperliquidProvider.stream will link to websockets in a later step")

    def latest(self) -> MarketSnapshot:
        raise NotImplementedError("HyperliquidProvider.latest will fetch REST snapshots in a later step")


__all__ = ["HyperliquidProvider"]
