# LangGraph Topology Blueprint

```
[Market Stream Fan-In]
    ├── Binance Stream Node
    ├── OKX Stream Node
    └── Hyperliquid Stream Node
         ↓ snapshot bus
[Feature Sampler]
    ├── Order-Book Imbalance Agent
    ├── Micro-Momentum Agent
    ├── Volatility & Regime Agent
    └── Cross-Venue Flow Agent
         ↓ signal envelopes
[Signal Router]
    ├── Memory Writer (vector + Redis summary)
    └── Risk Gatekeeper
         ↓ approved actions
[Execution Coordinator]
    ├── Smart Order Router
    └── Kill Switch + Alerting
         ↓ execution bus (dry-run by default)
[Notebook Observer]
    └── Strategy Recorder → `notebooks/`
```

## Coordination Notes
- `src/graph/crypto_workflow.py` materialises the LangGraph wrapper around `SignalRouter`, keeping signals and orders inside the state dictionary so downstream components can replay them.
- Use LangGraph conditional edges so the Risk Gatekeeper can halt execution without stopping feature updates.
- Persist concise state in a vector store (`VECTOR_DB_PATH`) plus Redis for low-latency counters.
- Each feature agent emits `(signal_value, confidence, diagnostics_ref)` to ease notebook playback.
- The Notebook Observer subscribes to the signal router and writes structured blobs for reproducible analysis.

## Memory Layout
- **Vector collection:** embeds rolling commentary summaries (`window=5min`).
- **Redis hashes:** store latest metrics per agent (imbalance skew, z-score, vol regime). Avoid `try/except`; validation happens at call sites.

## Error & Retry Policy
- Market streams restart via exchange-specific heartbeats. Failures bubble to the coordinator; only the Risk Gatekeeper decides on resume.
- Execution coordinator raises signals instead of catching exceptions. Supervisor handles process restarts.
