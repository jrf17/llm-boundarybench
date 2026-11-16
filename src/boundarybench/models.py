"""Core data models for BoundaryBench.

These dataclasses are the shared vocabulary between the synthetic application,
the deterministic backend, the scoring engine, and the reporters. They are
intentionally plain and serializable so that evidence can be written to JSON
reports without a marshalling layer.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DirectSource(StrEnum):
    """Where a behavior-directing instruction originated."""

    SYSTEM = "system"
    USER = "user"
    RETRIEVED = "retrieved"
    TOOL_OUTPUT = "tool_output"


class DecisionType(StrEnum):
    """What the simulated assistant decided to do with a turn."""

    NO_ACTION = "no_action"
    TOOL_CALL = "tool_call"
    RESPOND = "respond"


class AuthorizationStatus(StrEnum):
    """Outcome of the application-layer authorization check."""

    PERMITTED = "permitted"
    DENIED = "denied"
    NOT_REQUIRED = "not_required"


class ToolEffect(StrEnum):
    """Side-effect class of a simulated tool."""

    SENSITIVE = "sensitive"
    READ_ONLY = "read_only"


class ViolationType(StrEnum):
    """Classes of observable, scoreable security violations."""

    UNAUTHORIZED_TOOL = "unauthorized_tool"
    DISCLOSURE = "disclosure"
    INJECTION_FOLLOWED = "injection_followed"
    EXFILTRATION = "exfiltration"


@dataclass
class Directive:
    """A parsed behavior-directing instruction extracted from some input."""

    tool: str
    arguments: dict[str, Any]
    source: DirectSource
    confidence: float = 1.0


@dataclass
class ToolCall:
    """A tool invocation that the assistant intends to perform."""

    tool: str
    arguments: dict[str, Any]
    source: DirectSource


@dataclass
class ToolEvent:
    """A tool invocation that actually executed, with its authorization decision."""

    tool: str
    arguments: dict[str, Any]
    source: DirectSource
    authorized: bool
    outcome: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "arguments": self.arguments,
            "source": self.source.value,
            "authorized": self.authorized,
            "outcome": self.outcome,
        }


@dataclass
class RetrievalResult:
    """Documents selected by the retrieval workflow for a given query."""

    query: str
    documents: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Turn:
    """A single user turn plus everything the application did in response."""

    turn_id: str
    user_message: str
    response: str
    decision_type: DecisionType
    directives: list[Directive] = field(default_factory=list)
    tool_events: list[ToolEvent] = field(default_factory=list)
    retrieval: RetrievalResult | None = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "user_message": self.user_message,
            "response": self.response,
            "decision_type": self.decision_type.value,
            "directives": [
                {
                    "tool": d.tool,
                    "arguments": d.arguments,
                    "source": d.source.value,
                    "confidence": d.confidence,
                }
                for d in self.directives
            ],
            "tool_events": [e.to_dict() for e in self.tool_events],
            "retrieval": (
                {
                    "query": self.retrieval.query,
                    "documents": self.retrieval.documents,
                }
                if self.retrieval
                else None
            ),
            "timestamp": self.timestamp,
        }


def new_turn_id() -> str:
    return uuid.uuid4().hex
