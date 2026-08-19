# WANDR Product Goals and Success Metrics

## Priority Order

1. **Benchmark quality** — score validity, signal fidelity, and reproducibility are top priority.
2. **Developer usability** — task authoring and debugging must be fast and consistent.
3. **Cost efficiency** — prevent unbounded spend while preserving benchmark quality.
4. **Provider breadth** — keep multi-provider support broad but contract-driven.

## Measurable Targets

| Area | Metric | Target |
| --- | --- | --- |
| Run reliability | Trials without verifier/agent failure | >= 97% |
| Cost control | Estimated trial units blocked above guardrail | 100% |
| Reproducibility | Replay packs emitted for successful verifier runs | 100% |
| Evaluation turnaround | Validation config wall-clock completion | <= 6h |
| Observability | Jobs with machine-readable summary + failure taxonomy | 100% |
| Authoring quality | New scaffolded tasks with task metadata gates | 100% |

## Operating Policy

- Expensive configs (`validation`, `wandr`) require explicit acknowledgement.
- New task sources should be created with `./scripts/wandr scaffold-task ...`.
- Quality metadata (`task_meta.toml`) is validated when present and required for scaffolded tasks.
