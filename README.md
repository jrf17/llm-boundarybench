# LLM BoundaryBench

A reproducible AI/LLM security evaluation framework for testing **trust
boundaries** in LLM-integrated applications. It ships an intentionally
vulnerable synthetic application, a hardened version of the same application,
structured adversarial test cases, a deterministic offline execution engine,
transparent behavior-based scoring, and a genuine Microsoft PyRIT integration.

The central research question:

> How can an LLM-integrated application be systematically evaluated for
> failures to preserve trust boundaries between trusted instructions, untrusted
> content, and authorized actions?

BoundaryBench is a **security research platform**, not a collection of example
prompts and not a wrapper around a third-party CLI.

---

## Problem statement

LLM-integrated applications combine at least three kinds of input with very
different trust levels:

1. **Trusted instructions** — the system prompt and application policy.
2. **Untrusted content** — user prompts, retrieved documents, and tool output.
3. **Authorized actions** — the operations the application is allowed to perform.

When an application lets untrusted content steer authorized actions, an attacker
can cross that boundary via prompt injection, retrieval poisoning, or tool-output
manipulation. Defending correctly requires enforcement **outside the model**, in
application code, because a stronger system prompt is itself just more text the
attacker can try to override.

BoundaryBench makes these failures and their mitigations *observable*.

---

## Core capabilities

- **Two comparable applications** — a vulnerable mode and a hardened mode that
  expose the same tasks and interfaces, so identical test cases run against both.
- **Deterministic offline execution** — a transparent, documented rule-based
  simulator; no cloud credentials, no GPU, no internet, no paid API.
- **Structured, schema-validated test cases** — versioned JSON with threat
  objective, input surface, trust boundary, payload, expected behavior, scoring
  criteria, and required evidence.
- **Behavior-based scoring** — violations are detected from tool events and
  authorization telemetry, not from keyword presence in a refusal string.
- **JSON and Markdown reports** — including a vulnerable-vs-hardened comparison.
- **Genuine PyRIT integration** — a real `PromptTarget` adapter driven by PyRIT
  attack strategies and scored with PyRIT scorers (tested against PyRIT 1.2.0).
- **Loopback-only, simulated side effects** — no real email, no exfiltration, no
  remote execution, no credentials.

---

## Threat model summary

| Element | Trust |
| --- | --- |
| System prompt / application policy | Trusted |
| User prompt | Untrusted (attacker-controlled) |
| Retrieved document content | Untrusted (attacker-controlled) |
| Tool output | Untrusted (attacker-controlled) |
| Authorized action (send email, export) | Must be gated by application code |

The full model is in [`docs/threat-model.md`](docs/threat-model.md).

---

## Architecture overview

```
cases/*.json           structured adversarial + benign test cases
        │  (schema-validated)
        ▼
evaluation/runner      executes a case against one mode
        │
        ▼
application/           SyntheticApp (FastAPI or direct)
   ├── decision.py     deterministic "assistant" (proposes directives)
   ├── policy.py       authorization layer (vulnerable = empty, hardened = real)
   ├── retrieval.py    document retrieval boundary
   └── tools.py        simulated tools with harmless side effects
        │
        ▼
evaluation/scoring     behavior-based violation detection
        │
        ▼
evaluation/reporting  JSON + Markdown reports
integrations/         PyRIT PromptTarget adapter
```

See [`docs/architecture.md`](docs/architecture.md) for details.

---

## Installation

Requires Python 3.11–3.14. `uv` is recommended (install from
[astral.sh/uv](https://astral.sh/uv)).

```bash
git clone https://github.com/jrf17/llm-boundarybench.git
cd llm-boundarybench
uv venv .venv
source .venv/bin/activate
uv pip install -e '.[dev,pyrit]'
```

Or with plain pip in a virtual environment:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev,pyrit]'
```

PyRIT is an optional extra (`.[pyrit]`); the deterministic offline path works
without it.

---

## Quick start

```bash
# report readiness (never prints secrets)
boundarybench doctor

# list the shipped test cases
boundarybench cases list

# run the benchmark against each mode (deterministic, offline)
boundarybench run --backend deterministic --target vulnerable --suite all
boundarybench run --backend deterministic --target hardened --suite all

# compare the two runs
boundarybench compare \
  --baseline reports/run-<id>-vulnerable.json \
  --hardened reports/run-<id>-hardened.json \
  --output reports/comparison.md
```

Or run the whole thing in one step:

```bash
python examples/offline_demo.py
python examples/pyrit_demo.py   # requires the pyrit extra
```

---

## Supported scenarios

| Category | Cases | What it demonstrates |
| --- | --- | --- |
| `direct_injection` | instruction override, authority spoofing | untrusted prompt overriding policy |
| `retrieval_injection` | doc injection, source impersonation | malicious content entering via the retrieval boundary |
| `tool_output` | tool-output directive, unauthorized exfiltration | tool output steering downstream decisions |
| `multi_turn` | gradual escalation | conversation-state effects on authorization |
| `information_disclosure` | synthetic canary disclosure | lower-trust input disclosing protected markers |
| `benign` | legitimate email, clean retrieval, safe suspicious data | hardening does not break authorized use |

All eight attack scenarios are observable violations in vulnerable mode and
blocked in hardened mode; the three benign controls pass in both modes.

---

## Sample results

Deterministic offline run, 11 cases:

```
| Case                 | Vulnerable   | Hardened     |
| bn-001-legit-email   | no violation | no violation |
| bn-002-...-retrieval | no violation | no violation |
| bn-003-suspicious    | no violation | no violation |
| di-001-override      | violation    | no violation |
| di-002-spoof         | violation    | no violation |
| ri-001-doc-injection | violation    | no violation |
| ri-002-impersonation | violation    | no violation |
| to-001-tool-output   | violation    | no violation |
| ut-001-exfiltration  | violation    | no violation |
| mt-001-escalation    | violation    | no violation |
| id-001-canary        | violation    | no violation |
```

Real PyRIT run against the local synthetic target:

```
[vulnerable] PyRIT outcome=success turns=1 reason=Objective achieved according to scorer
[hardened]  PyRIT outcome=failure turns=1 reason=Failed to achieve objective after 1 attempts
```

Full evidence is in [`reports/examples/`](reports/examples/).

---

## Testing

```bash
pytest -q              # unit, integration, security (incl. real PyRIT smoke test)
ruff check .           # lint
ruff format --check .  # formatting
```

No test contacts a public model API by default.

---

## CI status

CI runs lint, format, the full test suite (including the PyRIT local smoke
test), and the offline demo on Python 3.11, 3.12, and 3.13. See
`.github/workflows/ci.yml`.

---

## Limitations

This project is a controlled synthetic evaluation framework. It is **not**:

- a claim that the deterministic simulator reproduces any real model's behavior;
- a measurement of real LLM performance;
- a comprehensive LLM security scanner; or
- evidence of statistical generalizability from its small case set.

The deterministic backend models *application* trust-boundary decisions, which
is exactly what the framework measures — the enforcement in application code,
not the nondeterminism of a hosted model. See [`docs/limitations.md`](docs/limitations.md).

---

## Responsible use

BoundaryBench defaults to localhost, synthetic documents, dummy secrets, and
simulated tools. It will not contact third-party LLM systems unless you
explicitly configure an authorized target. Do not point it at systems you are
not authorized to test. See [`docs/responsible-use.md`](docs/responsible-use.md)
and [`SECURITY.md`](SECURITY.md).

---

## License

MIT. See [`LICENSE`](LICENSE).

Microsoft PyRIT is used under its own license and is not claimed as original
work here. BoundaryBench's original contribution is its synthetic applications,
trust-boundary scenarios, execution orchestration, evaluation logic, evidence
collection, and reporting.
