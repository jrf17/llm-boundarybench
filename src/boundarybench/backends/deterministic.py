"""Deterministic offline execution backend.

Runs a test case's turns against the synthetic application (either mode) and
collects structured evidence. No model credentials, GPU, or network access are
required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from boundarybench.application.app import build_app
from boundarybench.models import Turn


@dataclass
class RunEvidence:
    case_id: str
    mode: str
    turns: list[Turn] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "mode": self.mode,
            "turns": [t.to_dict() for t in self.turns],
            "error": self.error,
        }


def run_case(case: dict[str, Any], mode: str) -> RunEvidence:
    """Execute a test case against the synthetic application in ``mode``."""
    app = build_app(mode)
    app.reset()
    turns: list[Turn] = []
    error: str | None = None

    try:
        for message in case["turns"]:
            turns.append(app.handle_turn(message))
    except Exception as exc:  # noqa: BLE001 - runner must capture and report
        error = f"{type(exc).__name__}: {exc}"

    return RunEvidence(case_id=case["id"], mode=mode, turns=turns, error=error)
