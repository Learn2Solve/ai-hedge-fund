"""OKX market data adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from ..models import MarketSnapshot
from .base import MarketDataProvider, StreamConfig
from .local_cache import LocalCacheProvider


@dataclass(slots=True)
class OKXProvider(MarketDataProvider):
    config: StreamConfig
    cache_dir: Path | None = None
    name: str = "okx"

    def __post_init__(self) -> None:
        self._delegate: LocalCacheProvider | None = None
        if self.cache_dir is not None:
            self._delegate = LocalCacheProvider(self.config, self.cache_dir, name=self.name)

    def stream(self, *, since: datetime | None = None) -> Iterable[MarketSnapshot]:
        if self._delegate is not None:
            return self._delegate.stream(since=since)
        raise NotImplementedError("Live OKX streaming will be implemented with websockets")

    def latest(self) -> MarketSnapshot:
        if self._delegate is not None:
            return self._delegate.latest()
        raise NotImplementedError("Live OKX REST fetching not implemented yet")


__all__ = ["OKXProvider"]
