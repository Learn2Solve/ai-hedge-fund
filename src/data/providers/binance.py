"""Binance market data adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from ..models import MarketSnapshot
from .base import MarketDataProvider, StreamConfig


@dataclass(slots=True)
class BinanceProvider(MarketDataProvider):
    config: StreamConfig
    name: str = "binance"

    def stream(self, *, since: datetime | None = None) -> Iterable[MarketSnapshot]:
        raise NotImplementedError("BinanceProvider.stream will link to websockets in a later step")

    def latest(self) -> MarketSnapshot:
        raise NotImplementedError("BinanceProvider.latest will fetch REST snapshots in a later step")


__all__ = ["BinanceProvider"]
