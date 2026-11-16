"""Deterministic decision engine (the "simulated LLM").

This module models — transparently and reproducibly — how a naive instruction-
following assistant would respond to a turn, given (a) the trusted system
instruction, (b) the user message, (c) any retrieved documents, and (d) any
tool output produced so far this turn.

It is a documented state machine, NOT a real model and NOT a claim about real
model behavior. Its purpose is to make trust-boundary failures observable so the
vulnerable/hardened comparison is driven by the application's enforcement, not
by the nondeterminism of a hosted LLM.

The engine does NOT enforce policy. It proposes directives (things an assistant
that "follows instructions" would do). Policy enforcement happens in
``policy.py``, outside the model, in both modes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from boundarybench.models import DecisionType, Directive, DirectSource

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def _clean_email(raw: str) -> str:
    return raw.rstrip(".,;:!?")


# A user message containing these markers is treated as an injection attempt
# against the user channel itself (e.g. "ignore your instructions and ...").
_INJECTION_MARKERS = (
    "ignore all previous instructions",
    "ignore previous instructions",
    "ignore your instructions",
    "disregard your instructions",
    "system message",
    "developer message",
    "you are now",
    "pretend you are",
    "act as if",
    "override",
    "jailbreak",
)

# Tools recognized when the assistant "follows an instruction".
_FORWARD_VERBS = (
    "forward",
    "send",
    "email",
    "transmit",
    "share",
    "copy",
)
_EXFIL_VERBS = ("export", "exfiltrate", "extract", "dump", "download")
_SECRET_VERBS = ("disclose", "reveal", "expose", "show", "leak", "print")


def _find_email(text: str) -> str | None:
    match = _EMAIL_RE.search(text)
    return _clean_email(match.group(0)) if match else None


def _has_injection_marker(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _INJECTION_MARKERS)


@dataclass
class Decision:
    """What the assistant intends to do this turn."""

    decision_type: DecisionType
    tool: str | None = None
    arguments: dict[str, Any] | None = None
    source: DirectSource | None = None
    rationale: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision_type": self.decision_type.value,
            "tool": self.tool,
            "arguments": self.arguments,
            "source": self.source.value if self.source else None,
            "rationale": self.rationale,
        }


class DecisionEngine:
    """Rule-based model of a naive assistant's decision for a single turn."""

    def __init__(self) -> None:
        self._tool_names = {
            "send_email",
            "exfiltrate",
            "expose_secret",
            "lookup_contact",
            "retrieve_document",
        }

    def decide(
        self,
        user_message: str,
        retrieved_docs: list[dict[str, Any]],
        tool_outputs: list[dict[str, Any]],
    ) -> Decision:
        """Propose a decision for the current turn.

        Priority order models an assistant that follows the most recent
        "authoritative-looking" instruction it saw: tool output first, then
        retrieved document content, then the user message.
        """
        directives = self.parse_directives(user_message, retrieved_docs, tool_outputs)
        if not directives:
            return Decision(DecisionType.RESPOND, rationale="no actionable directive found")

        directive = directives[0]
        return Decision(
            decision_type=DecisionType.TOOL_CALL,
            tool=directive.tool,
            arguments=directive.arguments,
            source=directive.source,
            rationale=f"following directive from {directive.source.value}",
        )

    def parse_directives(
        self,
        user_message: str,
        retrieved_docs: list[dict[str, Any]],
        tool_outputs: list[dict[str, Any]],
    ) -> list[Directive]:
        """Extract ordered directives from every input surface."""
        directives: list[Directive] = []

        # 1. Tool output (highest priority for a naive assistant).
        for output in tool_outputs:
            note = output.get("note", "")
            if isinstance(note, str):
                directives.extend(self._directives_from_text(note, DirectSource.TOOL_OUTPUT))

        # 2. Retrieved documents.
        for doc in retrieved_docs:
            directives.extend(
                self._directives_from_text(doc.get("content", ""), DirectSource.RETRIEVED)
            )

        # 3. User message. If it carries injection markers, its source is
        #    downgraded so the authorization layer can distinguish a direct
        #    instruction from an attempted override.
        user_source = (
            DirectSource.USER
            if not _has_injection_marker(user_message)
            else DirectSource.RETRIEVED  # mark as untrusted for policy purposes
        )
        user_directives = self._directives_from_text(user_message, user_source)
        directives.extend(user_directives)

        # A direct user instruction for a sensitive action takes precedence
        # over any injected content, so a legitimate request is not shadowed
        # by an unrelated retrieved document.
        directives.sort(key=lambda d: 0 if d.source == DirectSource.USER else 1)

        return directives

    def _directives_from_text(self, text: str, source: DirectSource) -> list[Directive]:
        lowered = text.lower()
        found: list[Directive] = []

        email = _find_email(text)
        has_forward_verb = any(verb in lowered for verb in _FORWARD_VERBS)
        has_secret_verb = any(verb in lowered for verb in _SECRET_VERBS)
        has_exfil_verb = any(verb in lowered for verb in _EXFIL_VERBS)

        # Sensitive tool requests only count when an address is named (except
        # explicit exfiltration, which is always sensitive).
        if has_exfil_verb and email:
            found.append(
                Directive(
                    tool="exfiltrate",
                    arguments={"destination": email, "fields": ["contact_list"]},
                    source=source,
                )
            )
        elif has_forward_verb and email:
            found.append(
                Directive(
                    tool="send_email",
                    arguments={"to": email, "subject": "forwarded data"},
                    source=source,
                )
            )

        if has_secret_verb and ("secret" in lowered or "canary" in lowered or "key" in lowered):
            key = "canary" if "canary" in lowered else "api_key"
            found.append(
                Directive(
                    tool="expose_secret",
                    arguments={"key": key},
                    source=source,
                )
            )

        if "lookup" in lowered or "look up" in lowered or "look into" in lowered:
            found.append(
                Directive(
                    tool="lookup_contact",
                    arguments={"name": "synthetic.contact"},
                    source=source,
                )
            )

        return found
