"""Placeholder script for caching market snapshots.

Once exchange adapters are implemented, this script will download a bounded
sample of order-book and trade data, then store it under `.cache/data` so the
notebooks can replay deterministic scenarios.
"""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    cache_dir = Path(".cache/data")
    cache_dir.mkdir(parents=True, exist_ok=True)
    # Actual sampling logic will follow once adapters land.
    print(f"Cache directory ready at {cache_dir}")


if __name__ == "__main__":
    main()
