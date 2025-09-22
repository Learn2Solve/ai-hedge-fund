# Notebooks

Each notebook reproduces a specific stage of the crypto HFT workflow:

1. **imbalance_scout.ipynb** – builds order-book features and sanity checks queue depth metrics.
2. **momentum_probe.ipynb** – explores short-horizon momentum and funding signals.
3. **volatility_regime.ipynb** – classifies volatility states and compares exchange vs. on-chain metrics.
4. **flow_monitor.ipynb** – visualises cross-venue spreads and flow anomalies.
5. **agent_playthrough.ipynb** – end-to-end replay of the LangGraph pipeline with cached data.

All notebooks expect cached parquet inputs under `.cache/data`. Generate the cache with `poetry run python scripts/cache_snapshot.py` (stub to arrive with data adapters). Rerun cells top-to-bottom after synchronising the repo; avoid manual edits to outputs so diffs stay clean.
