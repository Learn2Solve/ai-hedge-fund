# AI Crypto Market Maker

This branch retools the AI Hedge Fund framework for high-frequency crypto execution. The goal is to coordinate lean, specialized agents that ingest exchange order books, on-chain flows, and funding data to produce latency-aware trading signals. All work here is research-only; no orders are transmitted without explicit integration.

## Agent Topology
- **Order-Book Imbalance Agent** – tracks queue depth and cancel/replace activity to flag short-lived pressure.
- **Micro-Momentum Agent** – evaluates sub-second price/funding shifts for continuation or mean-revert edges.
- **Volatility & Regime Agent** – measures realized versus implied vol to adapt aggressiveness.
- **Flow Intelligence Agent** – detects cross-venue spreads, whale transactions, and CEX↔DEX bridges.
- **Execution & Risk Coordinators** – gate position sizes, enforce venue caps, and run kill-switches.

Agents communicate through LangGraph/LangChain with a vector memory layer so context persists across ticks. Analyses are documented as reproducible Jupyter notebooks under `notebooks/`.

## Install
```bash
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund
poetry install
```
Copy `.env.example` to `.env` and fill in exchange keys (`BINANCE_*`, `OKX_*`, `HYPERLIQUID_*`), on-chain providers (`HELIUS_API_KEY`, `TENDERLY_ACCESS_KEY`), and at least one LLM key for orchestration.

## Run
- **Backtester:** `poetry run python src/backtester.py --ticker BTCUSDT --start-date 2024-06-01`
- **Live loop (dry-run by default):** `poetry run python src/main.py --ticker BTCUSDT,ETHUSDT --ollama`
- **API:** `poetry run uvicorn app.backend.main:app --reload`

Add `--config configs/crypto.yml` once new adapters land. Execution remains sandboxed until risk checks clear the `DRY_RUN=false` flag.

## Development Workflow
Format with `poetry run black`, `poetry run isort`; lint via `poetry run flake8`. Tests live under `tests/` with fixtures in `tests/fixtures/`; run `poetry run pytest` before any pull request. Keep functions minimal and explicit—avoid `try`/`except` unless propagating a required fallback.

## Research Outputs
Each agent and strategy ships with a notebook demonstrating feature extraction, signal validation, and integration tests. Use `poetry run jupyter lab` to explore them; notebooks rely on cached snapshots created by `scripts/cache_snapshot.py` (coming soon).

## Disclaimer
This repository is for educational and research purposes only. It does not provide investment advice or guarantee performance. Never trade with real capital based solely on this code.
