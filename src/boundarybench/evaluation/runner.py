"""Execution engine: loads cases, runs them against both modes, scores them."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from boundarybench.backends.deterministic import run_case
from boundarybench.evaluation.scoring import Score, score_turn


@dataclass
class CaseResult:
    case_id: str
    case_name: str
    category: str
    mode: str
    violation: bool
    expected: str
    passed: bool
    score: Score
    turns: list[dict[str, Any]]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "case_name": self.case_name,
            "category": self.category,
            "mode": self.mode,
            "violation": self.violation,
            "expected": self.expected,
            "passed": self.passed,
            "score": self.score.to_dict(),
            "turns": self.turns,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CaseResult:
        score_data = data["score"]
        score = Score(
            violation=score_data["violation"],
            violation_type=score_data["violation_type"],
            rationale=score_data["rationale"],
        )
        return cls(
            case_id=data["case_id"],
            case_name=data["case_name"],
            category=data["category"],
            mode=data["mode"],
            violation=data["violation"],
            expected=data["expected"],
            passed=data["passed"],
            score=score,
            turns=data["turns"],
            error=data.get("error"),
        )


@dataclass
class RunReport:
    run_id: str
    backend: str
    target: str
    started_at: str
    results: list[CaseResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "backend": self.backend,
            "target": self.target,
            "started_at": self.started_at,
            "results": [r.to_dict() for r in self.results],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunReport:
        return cls(
            run_id=data["run_id"],
            backend=data["backend"],
            target=data["target"],
            started_at=data["started_at"],
            results=[CaseResult.from_dict(r) for r in data["results"]],
        )


def _expected_for(case: dict[str, Any], mode: str) -> str:
    return case["expected_vulnerable"] if mode == "vulnerable" else case["expected_hardened"]


def _any_turn_violates(turns: list[dict[str, Any]], case: dict[str, Any]) -> Score:
    scoring = case["scoring"]
    violation_type = scoring["violation_type"]
    marker = scoring.get("marker")

    # A multi-turn case is a violation if ANY turn violates.
    for turn_dict in turns:
        turn = _turn_from_dict(turn_dict)
        score = score_turn(turn, violation_type, marker)
        if score.violation:
            return score

    # Final turn determines "no violation" for reporting.
    if turns:
        return score_turn(_turn_from_dict(turns[-1]), violation_type, marker)
    return Score(False, None, "no turns executed")


def _turn_from_dict(d: dict[str, Any]) -> Any:
    from boundarybench.models import (
        DecisionType,
        Directive,
        DirectSource,
        RetrievalResult,
        ToolEvent,
        Turn,
    )

    return Turn(
        turn_id=d["turn_id"],
        user_message=d["user_message"],
        response=d["response"],
        decision_type=DecisionType(d["decision_type"]),
        directives=[
            Directive(
                tool=directive["tool"],
                arguments=directive["arguments"],
                source=DirectSource(directive["source"]),
                confidence=directive.get("confidence", 1.0),
            )
            for directive in d["directives"]
        ],
        tool_events=[
            ToolEvent(
                tool=e["tool"],
                arguments=e["arguments"],
                source=DirectSource(e["source"]),
                authorized=e["authorized"],
                outcome=e["outcome"],
            )
            for e in d["tool_events"]
        ],
        retrieval=(
            RetrievalResult(
                query=d["retrieval"]["query"],
                documents=d["retrieval"]["documents"],
            )
            if d.get("retrieval")
            else None
        ),
        timestamp=d.get("timestamp", 0.0),
    )


def run_suite(
    cases: list[dict[str, Any]],
    mode: str,
    backend: str = "deterministic",
    target: str | None = None,
) -> RunReport:
    """Run every case against one mode and produce a scored report."""
    report = RunReport(
        run_id=uuid.uuid4().hex[:12],
        backend=backend,
        target=target or mode,
        started_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    )

    for case in cases:
        evidence = run_case(case, mode)
        expected = _expected_for(case, mode)
        turns = [t.to_dict() for t in evidence.turns]

        if evidence.error:
            result = CaseResult(
                case_id=case["id"],
                case_name=case["name"],
                category=case["category"],
                mode=mode,
                violation=False,
                expected=expected,
                passed=False,
                score=Score(False, None, f"execution error: {evidence.error}"),
                turns=turns,
                error=evidence.error,
            )
        else:
            score = _any_turn_violates(turns, case)
            observed = "violation" if score.violation else "no_violation"
            passed = observed == expected
            result = CaseResult(
                case_id=case["id"],
                case_name=case["name"],
                category=case["category"],
                mode=mode,
                violation=score.violation,
                expected=expected,
                passed=passed,
                score=score,
                turns=turns,
            )

        report.results.append(result)

    return report
