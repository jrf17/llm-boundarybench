# Responsible Use

BoundaryBench is an authorized research framework for evaluating trust
boundaries in LLM-integrated applications. It is designed to be safe by default.

## Built-in restrictions

1. **Loopback by default.** The synthetic application binds to `127.0.0.1`
   only (`application/run.py`).
2. **Synthetic data.** Documents, contacts, and secrets are fabricated markers
   (`CANARY-SECRET-7F3A9B21`, `sk-synthetic-DEADBEEF`, `attacker@example.com`).
   No real credentials or client data exist anywhere in the repository.
3. **Simulated side effects.** No tool sends email, transmits data, or modifies
   the system. `exfiltrate` returns `{"simulated": True}`.
4. **No autonomous external access.** The deterministic backend and the PyRIT
   adapter drive the local application only. Nothing contacts a third-party LLM
   or a public endpoint without explicit configuration.

## Opt-in for live targets

BoundaryBench ships with no configured live model target. If you choose to run
live-model evaluation:

- use only targets you are explicitly authorized to test;
- treat a supplied URL as a configuration value, **not** as proof of
  authorization;
- keep payloads synthetic and harmless;
- do not send attack payloads to arbitrary public endpoints.

## What not to do

- Do not point this framework at a production system you do not own or are not
  authorized to test.
- Do not add real secrets, real client data, or real email/export targets.
- Do not present the deterministic simulator's output as measured real-LLM
  behavior.

The intentionally vulnerable application is for local research only and must
not be represented as suitable for production deployment.
