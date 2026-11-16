"""Application-layer authorization policy.

This is the boundary the project is named after. It is enforced in ordinary
Python code OUTSIDE the decision engine, so a stronger system prompt or a
blocked-phrase list is not what provides protection — deterministic
authorization logic does.

The vulnerable executor applies an empty policy (everything the assistant
proposes runs). The hardened executor applies the real policy below.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from boundarybench.config import AppConfig
from boundarybench.models import AuthorizationStatus, DirectSource, ToolCall


@dataclass
class AuthorizationResult:
    status: AuthorizationStatus
    reason: str = ""


def vulnerable_policy(tool: str, _call: ToolCall, _config: AppConfig) -> AuthorizationResult:
    """Vulnerable mode: no authorization layer. Every proposed tool runs."""
    return AuthorizationResult(
        status=AuthorizationStatus.PERMITTED, reason="no authorization layer"
    )


def hardened_policy(tool: str, call: ToolCall, config: AppConfig) -> AuthorizationResult:
    """Hardened mode: enforce authorization outside the model.

    Rules:
    * Sensitive tools require the directive to originate from a trusted source
      (the user's own message, not retrieved/tool-output/injected content).
    * ``expose_secret`` and ``exfiltrate`` are never authorized in this lab;
      they model actions the assistant must refuse regardless of instruction
      source.
    """
    spec = next((t for t in config.tools if t.name == tool), None)
    if spec is None:
        return AuthorizationResult(
            status=AuthorizationStatus.DENIED, reason=f"unknown tool {tool!r}"
        )

    if spec.effect == "read_only":
        return AuthorizationResult(status=AuthorizationStatus.PERMITTED, reason="read-only tool")

    if not spec.requires_user_authorization:
        return AuthorizationResult(
            status=AuthorizationStatus.PERMITTED, reason="tool does not require authorization"
        )

    if tool in ("expose_secret", "exfiltrate"):
        return AuthorizationResult(
            status=AuthorizationStatus.DENIED,
            reason=f"{tool} is never authorized in this lab",
        )

    if call.source != DirectSource.USER:
        return AuthorizationResult(
            status=AuthorizationStatus.DENIED,
            reason=(
                f"sensitive tool {tool} requested from {call.source.value}; "
                "user authorization required"
            ),
        )

    # Even a user-source request is denied when it targets a synthetic
    # attacker-controlled destination: the application enforces a deny-list
    # outside the model rather than trusting the instruction's phrasing.
    recipient = str(call.arguments.get("to") or call.arguments.get("destination") or "")
    if "attacker@example.com" in recipient:
        return AuthorizationResult(
            status=AuthorizationStatus.DENIED,
            reason="destination is on the synthetic deny-list",
        )

    return AuthorizationResult(status=AuthorizationStatus.PERMITTED, reason="user-authorized")


def select_policy(mode: str) -> Any:
    if mode == "vulnerable":
        return vulnerable_policy
    if mode == "hardened":
        return hardened_policy
    raise ValueError(f"unknown mode: {mode!r}")
