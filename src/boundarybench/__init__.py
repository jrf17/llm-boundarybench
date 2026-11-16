"""BoundaryBench — reproducible AI/LLM trust-boundary security evaluation.

This package provides:

* an intentionally vulnerable synthetic LLM application,
* a hardened version of the same application,
* a deterministic offline execution backend,
* structured, schema-validated adversarial test cases,
* a transparent scoring engine, and
* a genuine Microsoft PyRIT integration.

All network targets bind to loopback by default and every privileged action is
simulated. See docs/responsible-use.md before pointing any component at a
real system.
"""

from __future__ import annotations

__version__ = "0.1.0"
