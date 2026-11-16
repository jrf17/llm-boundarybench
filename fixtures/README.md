# Synthetic fixtures

BoundaryBench's fixtures (retrieval documents, tool responses, synthetic
markers) are defined inline in `src/boundarybench/config.py` and
`src/boundarybench/application/tools.py`. They are kept in code, not separate
files, because the deterministic backend must guarantee that the exact same
fixtures are used every run — a missing file or a checkout without submodules
would silently change results.

All fixtures are synthetic:

- `attacker@example.com`, `bob@example.com` — placeholder addresses.
- `CANARY-SECRET-7F3A9B21`, `sk-synthetic-DEADBEEF` — dummy markers.
- `kb-001` … `kb-003` — fabricated knowledge-base documents.

No real credentials, client data, or third-party content are included.
