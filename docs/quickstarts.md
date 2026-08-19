# Role-Based Quickstarts

## Task Author
1. `./scripts/wandr scaffold-task <task_name> --domain-tag <tag>`
2. Edit `reference/wandr_tasks/<task_name>/config.py` and prompt fragments.
3. Generate: `uv --no-config run --project adapters/wandr --locked wandr <task_name> --overwrite`
4. Validate: `./scripts/wandr check`

## Benchmark Runner
1. Fill `.env` keys.
2. Run low-cost sanity: `./scripts/wandr smoke-local`
3. Run validation: `WANDR_ACK_EXPENSIVE_CONFIG=1 ./scripts/wandr validate`
4. Summarize run: `uv --no-config run --locked python scripts/summarize_jobs.py`

## Provider Integrator
1. Add provider endpoint under `agents/relay/providers/<provider>/`.
2. Register in `relay.providers.PROVIDERS`.
3. Add contract checks in `scripts/validate_provider_contracts.py` and `scripts/validate_configs.py`.
4. Run checks: `./scripts/wandr check`
