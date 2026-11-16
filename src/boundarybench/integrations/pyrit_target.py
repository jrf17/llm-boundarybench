"""Genuine PyRIT target adapter for the synthetic BoundaryBench application.

This class implements PyRIT's ``PromptTarget`` interface so the local
synthetic application can be driven by PyRIT attack strategies (e.g.
``PromptSendingAttack``) and scored with PyRIT scorers. It is not a wrapper
around a third-party CLI and does not require any hosted model.

The adapter forwards the current user message (the last message piece of the
normalized conversation) to the synthetic application and returns the assistant
response as a PyRIT ``Message`` via ``construct_response_from_request``.

PyRIT is an optional dependency (``boundarybench[pyrit]``). Importing this
module without it raises a clear error rather than silently degrading.
"""

from __future__ import annotations

import logging
from typing import Any

from boundarybench.application.app import SyntheticApp, build_app

try:
    from pyrit.models import Message, construct_response_from_request
    from pyrit.models.messages.message_piece import MessagePiece
    from pyrit.prompt_target import PromptTarget, TargetCapabilities, TargetConfiguration
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "PyRIT is required for the BoundaryBench target adapter. "
        "Install it with: pip install 'boundarybench[pyrit]'"
    ) from exc

logger = logging.getLogger(__name__)


def _default_configuration() -> TargetConfiguration:
    caps = TargetCapabilities(
        supports_multi_turn=True,
        supports_multi_message_pieces=True,
        supports_system_prompt=True,
        supports_editable_history=False,
    )
    return TargetConfiguration(capabilities=caps)


class BoundaryBenchTarget(PromptTarget):
    """A PyRIT PromptTarget backed by the synthetic BoundaryBench application."""

    _DEFAULT_CONFIGURATION = _default_configuration()
    _DEFAULT_TRACE_ENABLED = False
    _SUPPORTS_TOOL_CALL_HISTORY = False
    supported_auth_modes = ("none",)

    def __init__(self, *, mode: str = "vulnerable", **kwargs: Any) -> None:
        self._app: SyntheticApp = build_app(mode)
        self._mode = mode
        super().__init__(model_name=f"boundarybench-{mode}", **kwargs)

    def reset_conversation(self) -> None:
        """Reset the synthetic application's conversation state."""
        self._app.reset()

    @classmethod
    def get_auth_mode_parameters(cls, *, auth_mode: str) -> dict[str, object]:
        return {}

    async def _send_prompt_to_target_async(
        self, *, normalized_conversation: list[Message]
    ) -> list[Message]:
        current = normalized_conversation[-1]
        request_piece: MessagePiece = current.message_pieces[-1]

        # The synthetic application has its own fixed trusted system prompt;
        # we forward only the user text as the attacker-controlled turn.
        user_text = request_piece.converted_value

        turn = self._app.handle_turn(user_text)

        return [
            construct_response_from_request(
                request=request_piece,
                response_text_pieces=[turn.response],
                prompt_metadata={"boundarybench_mode": self._mode},
            )
        ]


__all__ = ["BoundaryBenchTarget"]
