# Limitations

BoundaryBench is an honest, controlled evaluation framework. Its boundaries are
documented here so its results are not overstated.

## Deterministic simulator is not a model

The offline backend is a transparent, rule-based state machine that models how a
naive assistant reacts to injected instructions. It is **not** evidence of real
LLM susceptibility. Its purpose is to make trust-boundary failures observable so
the vulnerable/hardened comparison measures *application enforcement*, not model
nondeterminism.

## Small case set

The benchmark ships 11 cases. Per-case results are exact and reproducible, but
no statistical generalization is claimed. Adding cases extends coverage without
changing the framework.

## Synthetic, single-threaded scope

The synthetic application is a small, single-process FastAPI/direct-call app.
It does not exercise distributed systems, concurrency under load, or real RAG
over large corpora. It deliberately keeps the surface small so the trust
boundary is unambiguous.

## Simulated side effects

"send_email", "exfiltrate", and "expose_secret" are simulated and return
structured outcomes. They model the *decision to act*; they do not test a real
mail transport, real network egress, or real credential handling.

## Scoring is behavior-based, not semantic

Offline scoring uses observable telemetry (tool events, authorization, marker
disclosure). It does not use a judge model to assess whether a *textual*
response is harmful in a subtle way. That requires a live model and is outside
the offline path.

## PyRIT Crescendo requires a live model

`CrescendoAttack` needs an adversarial chat model and an editable-history
target, so it is documented but not executed offline. The fail-safe example is
not a completed Crescendo evaluation. See
[`pyrit-integration.md`](pyrit-integration.md) and the register in
[`outstanding-work.md`](outstanding-work.md).

## Not a scanner, not production hardening

BoundaryBench does not scan arbitrary systems, does not claim to find
vulnerabilities in third-party applications, and its hardened app is a teaching
demonstration of enforcement placement, not a production reference architecture.

## Version pinning

PyRIT is pinned to 1.2.0; its public API is evolving. A PyRIT upgrade must be
re-verified against the adapter before the pin changes.

Unfinished work and recommended follow-ups are listed in
[`outstanding-work.md`](outstanding-work.md), not here.
