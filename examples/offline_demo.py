"""Deterministic offline demo.

Runs the full benchmark suite against both modes using the deterministic
backend and prints a comparison. No model credentials, GPU, or network access
are required.

Usage:
    python examples/offline_demo.py
"""

from __future__ import annotations

from pathlib import Path

from boundarybench.cases.loader import CaseLoader
from boundarybench.evaluation.reporting import (
    render_comparison,
    write_json_report,
    write_markdown_report,
)
from boundarybench.evaluation.runner import run_suite

CASES_DIR = Path(__file__).resolve().parent.parent / "cases"
OUT_DIR = Path(__file__).resolve().parent.parent / "reports" / "examples"


def main() -> None:
    loader = CaseLoader()
    cases = loader.load_all([CASES_DIR])
    print(f"Loaded {len(cases)} test cases.")

    vulnerable = run_suite(cases, "vulnerable")
    hardened = run_suite(cases, "hardened")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json_report(vulnerable, OUT_DIR / "offline-vulnerable.json")
    write_json_report(hardened, OUT_DIR / "offline-hardened.json")
    write_markdown_report(vulnerable, OUT_DIR / "offline-vulnerable.md")
    write_markdown_report(hardened, OUT_DIR / "offline-hardened.md")

    print(render_comparison(vulnerable, hardened))
    print(f"\nReports written to {OUT_DIR}")


if __name__ == "__main__":
    main()
