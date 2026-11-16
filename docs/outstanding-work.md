# Outstanding work

This page is the register of work that is **not** part of the published core.
It is not a claim that those items are in progress, and it is not authorization
to start them. Do not treat an item here as a defect in the deterministic
benchmark unless the item says the current path is unfinished.

Limitations of what the current results can prove are in
[`limitations.md`](limitations.md). This page records unfinished features and
recommended follow-ups so they are not only in chat.

## Published core (done)

These are implemented and verified offline, with no model credentials:

- Vulnerable and hardened synthetic applications, differing only in
  `application/policy.py`.
- Deterministic execution, schema-validated cases, behavior-based scoring, and
  JSON/Markdown comparison reports.
- PyRIT 1.2.0 `PromptTarget` adapter exercised by `PromptSendingAttack` against
  the local synthetic target (`examples/pyrit_demo.py`,
  `tests/security/test_pyrit.py`).
- CI on Python 3.11, 3.12, and 3.13.

## Unfinished: live PyRIT Crescendo

Status: wired, not executed.

`examples/crescendo_demo.py` constructs PyRIT's real `CrescendoAttack` and
exits 2 when `BOUNDARYBENCH_ADVERSARIAL_TARGET` is unset. That fail-safe is
tested. A genuine Crescendo run has not been performed.

Two separate requirements remain, and satisfying only one is not enough:

1. An explicitly authorized adversarial chat model. The repository ships none.
2. An objective target that natively supports multi-turn conversation and
   editable history. `BoundaryBenchTarget` declares
   `supports_editable_history=False`, so PyRIT's `CrescendoAttack` will reject
   it even if an adversarial model is configured. A real run needs a different
   PyRIT target, or a deliberate capability change plus tests that the history
   semantics match Crescendo's backtracking. Do not flip the capability flag
   without that work and call the existing example a completed Crescendo
   evaluation.

## Unfinished: live-model evaluation

Status: not implemented.

No live model target, endpoint, or credential path is configured. The
deterministic backend is the only executed evaluation path. A supplied URL is
not authorization to send prompts.

A future live path, if requested, must stay opt-in, loopback-or-allowlisted,
timeout-bounded, and separate from the offline results. It must not be reported
as measured LLM performance until a real authorized run exists.

## Recommended follow-ups (not started)

These were identified as useful extensions. None of them is required for the
published core, and none should be described as implemented.

- More adversarial cases (additional retrieval fixtures, multi-document
  retrieval, further role-spoof variants). The current set is 11 cases.
- A real-model backend behind the same application interface, still enforced
  outside the model, so the vulnerable/hardened comparison can be repeated
  against an authorized model.
- Judge-model or other PyRIT LLM scorers for live targets. Offline scoring
  stays telemetry-based; a judge score must not replace an observed tool event.
- CI coverage for Python 3.14. The package allows `>=3.11,<3.15` and local
  development used 3.14, but `.github/workflows/ci.yml` currently runs 3.11,
  3.12, and 3.13 only.

## Re-entry

Start an item above only when it is explicitly requested. Keep any new live
path out of the default `pytest` and `boundarybench run` commands.
