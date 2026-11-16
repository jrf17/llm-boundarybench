# AGENTS.md

Guidance for coding agents (and humans) maintaining this repository.

## Project nature

BoundaryBench is a local, synthetic, non-destructive AI security research
framework. Its default environment binds to loopback and uses simulated tools
with harmless side effects. Never introduce real credentials, real client data,
public live targets, or real side effects.

## Invariants

1. **Same tasks, same interfaces, different enforcement.** The vulnerable and
   hardened modes differ only in the authorization policy
   (`application/policy.py`). A change that makes the two modes diverge in any
   other way breaks the comparison the whole project is built on.
2. **Enforcement lives outside the model.** Hardening is done in deterministic
   application code, not in a stronger system prompt or a phrase block-list.
3. **Behavior-based scoring.** Violations are detected from tool events and
   authorization telemetry. Do not add scoring that equates "the assistant said
   no" with "the action was blocked" — check the telemetry.
4. **Deterministic offline path stays credential-free.** `boundarybench run`
   and `pytest` must work with no environment variables, no GPU, no network.
5. **Test cases are schema-validated.** Every case under `cases/` must pass
   `CaseLoader` (`boundarybench doctor`).

## Layout

- `src/boundarybench/application/` — the synthetic app (decision engine, policy,
  retrieval, tools, FastAPI layer).
- `src/boundarybench/evaluation/` — runner, scoring, reporting.
- `src/boundarybench/integrations/` — PyRIT adapter.
- `cases/` — JSON test cases, one directory per category.
- `tests/unit|integration|security` — pytest.
- `reports/examples/` — committed sample reports; regenerate with
  `python examples/offline_demo.py`.

## Adding a test case

1. Create `cases/<category>/<id>.json` following the schema in
   `cases/loader.py`.
2. Ensure the payload enters through the intended boundary (a retrieval case
   must arrive via a retrieved document, not a user prompt).
3. Run `boundarybench doctor` to validate, then `pytest -q`.

## Checks before commit

```bash
ruff check . && ruff format --check . && pytest -q
```

## PyRIT

The adapter in `integrations/pyrit_target.py` is tested against PyRIT 1.2.0.
When upgrading PyRIT, re-verify `PromptTarget`'s interface
(`_send_prompt_to_target_async`, `TargetConfiguration`, `TargetCapabilities`,
`construct_response_from_request`) before bumping the pin.
