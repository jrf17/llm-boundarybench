"""Command-line interface for BoundaryBench.

Commands: doctor, cases list, run, compare.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from boundarybench import __version__

_CASES_DIR = Path(__file__).resolve().parent.parent.parent / "cases"


def _default_cases_dir() -> Path:
    return _CASES_DIR


def cmd_doctor(args: argparse.Namespace) -> int:
    from boundarybench.cases.loader import CaseLoader, CaseValidationError

    print("BoundaryBench doctor")
    print(f"  version: {__version__}")

    try:
        loader = CaseLoader()
        cases = loader.load_all([_default_cases_dir()])
        print(f"  test cases: {len(cases)} valid")
    except CaseValidationError as exc:
        print(f"  test cases: INVALID\n{exc}")
        return 1

    try:
        import fastapi  # noqa: F401
        import jsonschema  # noqa: F401

        print("  core dependencies: ok (fastapi, jsonschema)")
    except ImportError as exc:
        print(f"  core dependencies: MISSING ({exc.name})")
        return 1

    try:
        import pyrit  # noqa: F401

        print(f"  pyrit: {pyrit.__version__}")
    except ImportError:
        print("  pyrit: not installed (optional; pip install 'boundarybench[pyrit]')")

    print("  network targets: loopback-only by default (no live-model config detected)")
    return 0


def cmd_cases_list(args: argparse.Namespace) -> int:
    from boundarybench.cases.loader import CaseLoader

    loader = CaseLoader()
    cases = loader.load_all([_default_cases_dir()])
    for case in cases:
        print(f"{case['id']:24} {case['category']:22} {case['name']}")
    print(f"\n{len(cases)} cases")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from boundarybench.cases.loader import CaseLoader
    from boundarybench.evaluation.reporting import write_json_report, write_markdown_report
    from boundarybench.evaluation.runner import run_suite

    if args.target not in ("vulnerable", "hardened"):
        print(
            f"error: --target must be 'vulnerable' or 'hardened', got {args.target!r}",
            file=sys.stderr,
        )
        return 2

    loader = CaseLoader()
    cases = loader.load_all([_default_cases_dir()])

    if args.suite and args.suite != "all":
        cases = [c for c in cases if c["category"] == args.suite]

    report = run_suite(cases, mode=args.target, backend=args.backend, target=args.target)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"run-{report.run_id}-{args.target}.json"
    md_path = out_dir / f"run-{report.run_id}-{args.target}.md"
    write_json_report(report, json_path)
    write_markdown_report(report, md_path)

    passed = sum(1 for r in report.results if r.passed)
    print(
        f"ran {len(report.results)} cases against {args.target}: {passed} passed, {len(report.results) - passed} failed"
    )
    print(f"  json: {json_path}")
    print(f"  markdown: {md_path}")
    return 0 if passed == len(report.results) else 1


def cmd_compare(args: argparse.Namespace) -> int:
    from boundarybench.evaluation.reporting import render_comparison
    from boundarybench.evaluation.runner import RunReport

    baseline = RunReport.from_dict(json.loads(Path(args.baseline).read_text()))
    hardened = RunReport.from_dict(json.loads(Path(args.hardened).read_text()))
    text = render_comparison(baseline, hardened)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
        print(f"wrote comparison to {out}")
    else:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="boundarybench",
        description="LLM BoundaryBench — reproducible AI/LLM trust-boundary security evaluation",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="report dependency and configuration readiness").set_defaults(
        func=cmd_doctor
    )

    cases = sub.add_parser("cases", help="manage test cases")
    cases_sub = cases.add_subparsers(dest="cases_command", required=True)
    cases_sub.add_parser("list", help="list test cases").set_defaults(func=cmd_cases_list)

    run = sub.add_parser("run", help="run the benchmark against one target mode")
    run.add_argument("--backend", default="deterministic", help="execution backend")
    run.add_argument("--target", required=True, choices=["vulnerable", "hardened"])
    run.add_argument("--suite", default="all", help="case category or 'all'")
    run.add_argument("--output", default="reports", help="output directory")
    run.set_defaults(func=cmd_run)

    cmp = sub.add_parser("compare", help="compare a vulnerable and a hardened report")
    cmp.add_argument("--baseline", required=True, help="vulnerable JSON report")
    cmp.add_argument("--hardened", required=True, help="hardened JSON report")
    cmp.add_argument("--output", default=None, help="write markdown to file")
    cmp.set_defaults(func=cmd_compare)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
