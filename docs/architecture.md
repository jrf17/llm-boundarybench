# Architecture

BoundaryBench separates five responsibilities so each can be reasoned about and
tested independently.

```
                    ┌─────────────────────────────────────┐
                    │  cases/  (schema-validated JSON)     │
                    └──────────────────┬──────────────────┘
                                       │ CaseLoader
                    ┌──────────────────▼──────────────────┐
                    │  evaluation/runner                  │
                    │  - selects target + mode            │
                    │  - runs turns, collects evidence    │
                    └──────────────────┬──────────────────┘
                                       │ SyntheticApp.handle_turn
                    ┌──────────────────▼──────────────────┐
                    │  application/                       │
                    │  ┌─────────────┐  ┌──────────────┐  │
                    │  │ decision.py │→ │ policy.py    │  │
                    │  │ (proposes)  │  │ (authorizes) │  │
                    │  └─────────────┘  └──────┬───────┘  │
                    │   retrieval.py          tools.py    │
                    │   (documents)        (simulated)     │
                    └──────────────────┬──────────────────┘
                                       │ Turn evidence
                    ┌──────────────────▼──────────────────┐
                    │  evaluation/scoring                 │
                    │  - behavior-based violation checks  │
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │  evaluation/reporting (JSON + MD)   │
                    └─────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
                    │  integrations/pyrit_target.py       │
                    │  PyRIT PromptTarget → SyntheticApp  │
                    └─────────────────────────────────────┘
```

## Components

### `application/decision.py` — the deterministic "assistant"

A documented rule-based state machine that models how a naive
instruction-following assistant responds to a turn. It parses directives from
three surfaces — tool output, retrieved documents, and the user message — and
proposes a tool call. It **does not enforce policy**.

This is deliberately not a real model and is not presented as one. Its job is to
make the trust-boundary failure *observable* so the comparison measures
application enforcement, not model nondeterminism.

### `application/policy.py` — the authorization layer

The boundary the project is named after. Two policies:

- `vulnerable_policy` — permits everything the assistant proposes (no layer).
- `hardened_policy` — enforces, in ordinary code, outside the model:
  - read-only tools are allowed;
  - `expose_secret` and `exfiltrate` are never authorized;
  - sensitive tools require a user-source directive;
  - a synthetic deny-list blocks known attacker destinations.

### `application/retrieval.py` — the retrieval boundary

A deterministic document corpus keyed by `doc_id`. A query selects a document
when it names its id, so attacker content genuinely arrives via the retrieved
document (never via the user prompt) and benign queries cannot accidentally pull
injected content.

### `application/tools.py` — simulated tools

Every tool returns a structured outcome and performs no real side effect.
Some outcomes carry an attacker-controllable `note` so tool-output injection can
be tested exactly as real tool output re-enters an LLM context.

### `application/app.py` — the orchestrator

Identical in both modes except for the policy it receives. It runs the
retrieve → decide → authorize → execute loop (bounded iterations, duplicate
directives skipped), and emits a `Turn` with full telemetry.

### `evaluation/` — runner, scoring, reporting

- `runner.py` runs a case against one mode and scores it.
- `scoring.py` maps violation types to concrete evidence checks on the telemetry.
- `reporting.py` writes JSON, Markdown, and a vulnerable-vs-hardened comparison.

### `integrations/pyrit_target.py` — the PyRIT adapter

Implements PyRIT's `PromptTarget` interface so PyRIT attacks can drive the local
synthetic app directly. See [`pyrit-integration.md`](pyrit-integration.md).

## Why not a stronger system prompt?

A stronger system prompt is still text the attacker can attempt to override.
BoundaryBench hardens by enforcing authorization in deterministic code, which an
injected instruction cannot rewrite. The vulnerable/hardened comparison isolates
exactly this difference.
