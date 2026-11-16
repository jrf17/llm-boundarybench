"""Synthetic application orchestrator (shared by vulnerable and hardened modes).

The orchestration is identical in both modes; the ONLY difference is the
authorization policy passed in. This makes the vulnerable/hardened comparison
measure enforcement, not incidental differences in application logic.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from boundarybench.application.decision import Decision, DecisionEngine
from boundarybench.application.policy import select_policy
from boundarybench.application.retrieval import retrieve
from boundarybench.application.tools import run_tool
from boundarybench.config import AppConfig
from boundarybench.models import (
    AuthorizationStatus,
    DecisionType,
    Directive,
    ToolCall,
    ToolEvent,
    Turn,
    new_turn_id,
)

logger = logging.getLogger(__name__)

_MAX_ITERATIONS = 5


class SyntheticApp:
    """The synthetic LLM-integrated assistant under test."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.engine = DecisionEngine()
        self.policy: Callable[..., Any] = select_policy(config.mode)
        self._turns: list[Turn] = []

    @property
    def mode(self) -> str:
        return self.config.mode

    @property
    def turns(self) -> list[Turn]:
        return list(self._turns)

    def reset(self) -> None:
        self._turns.clear()

    def handle_turn(self, user_message: str) -> Turn:
        """Process one user turn and return the full evidence record."""
        turn_id = new_turn_id()
        retrieval = retrieve(user_message, self.config)
        retrieved_docs = retrieval.documents

        directives: list[Directive] = []
        tool_events: list[ToolEvent] = []
        tool_outputs: list[dict[str, Any]] = []
        first_decision: Decision | None = None
        processed: set[tuple[str, tuple[tuple[str, str], ...]]] = set()

        for _ in range(_MAX_ITERATIONS):
            candidates = self.engine.parse_directives(user_message, retrieved_docs, tool_outputs)

            # Pick the first directive we have not already acted on. The list
            # is sorted user-first, then by injected source priority, so a
            # legitimate user instruction wins, and a duplicate directive is
            # skipped rather than treated as a stop condition.
            chosen: Directive | None = None
            for directive in candidates:
                signature = (
                    directive.tool,
                    tuple(sorted((str(k), str(v)) for k, v in directive.arguments.items())),
                )
                if signature in processed:
                    continue
                chosen = directive
                break

            if chosen is None:
                break

            decision = Decision(
                decision_type=DecisionType.TOOL_CALL,
                tool=chosen.tool,
                arguments=chosen.arguments,
                source=chosen.source,
                rationale=f"following directive from {chosen.source.value}",
            )
            if first_decision is None:
                first_decision = decision

            assert decision.tool is not None and decision.arguments is not None
            assert decision.source is not None

            signature = (
                decision.tool,
                tuple(sorted((str(k), str(v)) for k, v in decision.arguments.items())),
            )
            processed.add(signature)

            call = ToolCall(
                tool=decision.tool,
                arguments=decision.arguments,
                source=decision.source,
            )
            directives.append(
                Directive(
                    tool=decision.tool,
                    arguments=decision.arguments,
                    source=decision.source,
                )
            )

            auth = self.policy(decision.tool, call, self.config)
            authorized = auth.status == AuthorizationStatus.PERMITTED

            outcome: dict[str, Any] = {}
            if authorized:
                outcome = run_tool(decision.tool, decision.arguments, self.config)
                tool_outputs.append(outcome)
            else:
                outcome = {"denied_reason": auth.reason}

            tool_events.append(
                ToolEvent(
                    tool=decision.tool,
                    arguments=decision.arguments,
                    source=decision.source,
                    authorized=authorized,
                    outcome=outcome,
                )
            )

            # A denied sensitive action ends the turn in hardened mode; a
            # permitted action's output may itself carry a new directive.
            if not authorized:
                break

        response = self._compose_response(
            user_message=user_message,
            retrieved_docs=retrieved_docs,
            tool_events=tool_events,
            tool_outputs=tool_outputs,
        )

        turn = Turn(
            turn_id=turn_id,
            user_message=user_message,
            response=response,
            decision_type=first_decision.decision_type if first_decision else DecisionType.RESPOND,
            directives=directives,
            tool_events=tool_events,
            retrieval=retrieval,
        )
        self._turns.append(turn)
        logger.info("turn %s mode=%s events=%d", turn_id, self.mode, len(tool_events))
        return turn

    def _compose_response(
        self,
        *,
        user_message: str,
        retrieved_docs: list[dict[str, Any]],
        tool_events: list[ToolEvent],
        tool_outputs: list[dict[str, Any]],
    ) -> str:
        denied = [e for e in tool_events if not e.authorized]
        executed = [e for e in tool_events if e.authorized]

        if denied and not executed:
            return self.config.blocked_reply

        if executed:
            parts: list[str] = []
            for event in executed:
                parts.append(f"[tool:{event.tool}] authorized")
                if event.tool == "expose_secret":
                    value = event.outcome.get("value")
                    if value:
                        parts.append(f"protected value: {value}")
                elif event.tool == "send_email":
                    parts.append(f"simulated email to {event.outcome.get('to')}")
                elif event.tool == "exfiltrate":
                    parts.append(f"simulated copy to {event.outcome.get('destination')}")
            return " ".join(parts)

        if retrieved_docs:
            return f"Retrieved {len(retrieved_docs)} document(s) relevant to your query."

        return self.config.default_reply


def build_app(mode: str, **overrides: Any) -> SyntheticApp:
    """Construct a validated app instance for a mode."""
    from boundarybench.config import build_config

    return SyntheticApp(build_config(mode=mode, **overrides))  # type: ignore[arg-type]
