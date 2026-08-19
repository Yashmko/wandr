# Troubleshooting Decision Tree

## Run failed before scoring
- Check `verifier/error.json`.
- If missing submissions -> verify required `results_<task>.jsonl` files exist and are non-empty.
- If provider failure -> inspect `agent/status.json` and `agent/events.jsonl` restart taxonomy.

## Run finished but score is unexpectedly low
- Inspect `reward-details.json` and `wandr-details.json` quality signals.
- Inspect `report.html` for scoremap and field decomposition hot spots.

## High spend risk
- Use guardrail estimates before run.
- For expensive configs, require `WANDR_ACK_EXPENSIVE_CONFIG=1`.
- Optionally set `WANDR_MAX_TRIAL_UNITS` and `WANDR_MAX_CONCURRENT_TRIALS`.

## Regression investigation
- Generate machine-readable summary via `scripts/summarize_jobs.py`.
- Compare `failure_taxonomy`, token/cost totals, and provider comparison sections.
