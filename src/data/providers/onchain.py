"""On-chain flow and funding signals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from ..models import MarketSnapshot
from .base import MarketDataProvider, StreamConfig


@dataclass(slots=True)
class OnChainProvider(MarketDataProvider):
    config: StreamConfig
    name: str = "onchain"

    def stream(self, *, since: datetime | None = None) -> Iterable[MarketSnapshot]:
        raise NotImplementedError("OnChainProvider.stream will connect to RPC/webhooks in a later step")

    def latest(self) -> MarketSnapshot:
        raise NotImplementedError("OnChainProvider.latest will fetch the newest on-chain metrics")


__all__ = ["OnChainProvider"]
