# Contributing

Contributions that keep the project a reproducible, evidence-driven evaluation
framework are welcome.

## Principles

- Keep the default environment local, synthetic, and non-destructive.
- Do not add real credentials, real client data, or public live targets.
- Prefer observable, telemetry-backed evidence over keyword matching.
- Keep the deterministic offline path running without any hosted model.

## Development setup

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e '.[dev,pyrit]'
```

## Checks

```bash
pytest -q          # unit, integration, and security tests
ruff check .       # lint
ruff format --check .  # formatting
```

## Adding a test case

1. Write a JSON case under `cases/<category>/` following the schema in
   `src/boundarybench/cases/loader.py`.
2. Validate it: `boundarybench doctor`.
3. Add regression tests if the case exercises new behavior.

Test cases must use synthetic markers and harmless simulated tool effects only.
