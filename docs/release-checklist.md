# Release Checklist

- [ ] `./scripts/wandr check`
- [ ] `uv --no-config run --locked python scripts/validate_provider_contracts.py`
- [ ] `uv --no-config run --locked python scripts/relay_mock_smoke.py`
- [ ] Dataset digest consistency verified (`adapters/wandr` consistency check)
- [ ] Config validation passes (`scripts/validate_configs.py`)
- [ ] CI checks workflow green
