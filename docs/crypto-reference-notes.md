# Crypto Reference Integration Notes

Source reference: `/Users/mathinvariant/codes/crypto/hft/hft_crypto_mm` (polars-based imbalance research toolkit).

## Candidate Modules to Reuse
- `core/feature_pipeline.py`: end-to-end Parquet loader → atom/derived feature builder. Port to `src/data/pipelines/feature_pipeline.py`, swapping in our data adapters.
- `core/resampling.py`: temporal resampler abstractions worth adapting for event-driven backtests.
- `core/events.py`, `core/baseterms.py`, `core/derived.py`: modular feature builders; keep API signatures but convert to dataclasses for LangGraph nodes.
- `core/targets.py`, `core/technical_analysis.py`: target/indicator generators reusable for regime and momentum agents.
- `tools/imbalance_model.py`: ridge/LightGBM ensemble helpers; integrate into notebooks and optional research agent.
- `tools/feature_explorer.py`, `tools/alpha_profile_plotter.py`: quick visual diagnostics for notebooks.

## Data & Asset Notes
- `data/*/*.parquet`: order book + trade snapshots; treat as sample fixtures for `tests/fixtures/market/`.
- `feature_explore.ipynb`, `docs/return.md`: baseline notebooks to reproduce in `notebooks/` with new adapters.
- Chinese-language guide `特征工程文档.md`: translate key sections into future docs if needed.

## Dependency Gaps
- Adds `polars`, `scikit-learn`, `lightgbm` (optional), `seaborn`. Update `pyproject.toml` once the feature pipeline lands.
- Evaluate whether to keep both Polars and Pandas or standardise on one for performance.

## Integration Sketch
1. Wrap existing Parquet readers with new exchange streaming buffers; expose `TradeBatch` / `OrderBookSnapshot` models.
2. Convert feature builders into pure functions returning `pd.DataFrame | pl.DataFrame` with type hints to ease testing.
3. Register each feature block as a LangGraph node and save embeddings/logs to the shared vector store (`CryptoWorkflow` now demonstrates the interface).
4. Re-create `feature_explore.ipynb` as `notebooks/imbalance_scout.ipynb`, referencing cached datasets (placeholder notebooks are included). 
5. Port imbalance ridge workflow into `agents/imbalance/model.py` with config dataclasses and deterministic tests.
