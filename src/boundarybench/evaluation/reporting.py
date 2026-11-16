"""JSON and Markdown report generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from boundarybench.evaluation.runner import RunReport


def write_json_report(report: RunReport, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return path


def _fmt_reason(reason: str) -> str:
    return reason if reason else "-"


def render_markdown(report: RunReport) -> str:
    lines: list[str] = []
    lines.append(f"# BoundaryBench run {report.run_id}")
    lines.append("")
    lines.append(f"- Backend: `{report.backend}`")
    lines.append(f"- Target mode: `{report.target}`")
    lines.append(f"- Started: `{report.started_at}`")
    lines.append(f"- Cases: {len(report.results)}")
    lines.append("")

    passed = sum(1 for r in report.results if r.passed)
    lines.append(f"## Summary: {passed}/{len(report.results)} cases behaved as expected")
    lines.append("")
    lines.append("| Case | Category | Violation | Expected | Result | Rationale |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for r in report.results:
        mark = "PASS" if r.passed else "FAIL"
        lines.append(
            f"| `{r.case_id}` | {r.category} | "
            f"{'yes' if r.violation else 'no'} | {r.expected} | {mark} | "
            f"{_fmt_reason(r.score.rationale)} |"
        )
    lines.append("")

    lines.append("## Per-case evidence")
    lines.append("")
    for r in report.results:
        lines.append(f"### {r.case_id} — {r.case_name}")
        lines.append("")
        for i, turn in enumerate(r.turns, start=1):
            lines.append(f"**Turn {i}** — `{turn['user_message']}`")
            lines.append("")
            lines.append(f"Response: {turn['response']}")
            lines.append("")
            events = turn["tool_events"]
            if events:
                lines.append("| Tool | Source | Authorized | Outcome |")
                lines.append("| --- | --- | --- | --- |")
                for e in events:
                    outcome = e.get("outcome", {})
                    if isinstance(outcome, dict):
                        outcome_str = (
                            outcome.get("to")
                            or outcome.get("value")
                            or outcome.get("denied_reason", "")
                        )
                    else:
                        outcome_str = str(outcome)
                    lines.append(
                        f"| {e['tool']} | {e['source']} | "
                        f"{'yes' if e['authorized'] else 'no'} | {outcome_str} |"
                    )
                lines.append("")
        lines.append("")

    return "\n".join(lines)


def write_markdown_report(report: RunReport, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(report), encoding="utf-8")
    return path


def render_comparison(baseline: RunReport, hardened: RunReport) -> str:
    lines: list[str] = []
    lines.append("# BoundaryBench vulnerable vs hardened comparison")
    lines.append("")
    lines.append(f"- Baseline (vulnerable) run: `{baseline.run_id}`")
    lines.append(f"- Hardened run: `{hardened.run_id}`")
    lines.append("")

    by_case: dict[str, dict[str, Any]] = {}
    for r in baseline.results:
        by_case.setdefault(r.case_id, {})["vulnerable"] = r
    for r in hardened.results:
        by_case.setdefault(r.case_id, {})["hardened"] = r

    lines.append("| Case | Category | Vulnerable | Hardened | Control effect |")
    lines.append("| --- | --- | --- | --- | --- |")
    for case_id in sorted(by_case):
        entry = by_case[case_id]
        v = entry.get("vulnerable")
        h = entry.get("hardened")
        first = v if v is not None else h
        if first is None:
            continue
        v_txt = f"{'violation' if v and v.violation else 'no violation'}"
        h_txt = f"{'violation' if h and h.violation else 'no violation'}"
        if v and h and v.violation != h.violation:
            effect = "hardened control changed outcome"
        elif v and h and v.violation and h.violation:
            effect = "vulnerable behavior persists (control ineffective)"
        elif v and h and not v.violation and not h.violation:
            effect = "no violation in either mode"
        else:
            effect = "unexpected divergence"
        lines.append(f"| `{case_id}` | {first.category} | {v_txt} | {h_txt} | {effect} |")
    lines.append("")
    return "\n".join(lines)
