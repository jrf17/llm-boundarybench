"""FastAPI wrapper for the synthetic application.

Binds to loopback only (see ``run.py`` / uvicorn configuration) and exposes
telemetry in every response so external observers (and the PyRIT adapter) can
see authorization decisions and tool events, not just final text.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from boundarybench.application.app import build_app
from boundarybench.config import Mode

_apps: dict[str, Any] = {}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    reset: bool = False


class ChatResponse(BaseModel):
    mode: str
    response: str
    turn: dict[str, Any]


def get_app(mode: Mode) -> Any:
    if mode not in _apps:
        _apps[mode] = build_app(mode)
    return _apps[mode]


def create_app(mode: Mode | None = None) -> FastAPI:
    """Create the ASGI app. If ``mode`` is given, that single mode is served."""
    app = FastAPI(
        title="LLM BoundaryBench Synthetic Application",
        version="0.1.0",
        description=(
            "Intentionally vulnerable and hardened synthetic LLM assistant "
            "for local trust-boundary testing."
        ),
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/chat")
    async def chat(request: ChatRequest) -> ChatResponse:
        effective_mode: Mode = mode or "vulnerable"
        if effective_mode not in ("vulnerable", "hardened"):
            raise HTTPException(status_code=400, detail=f"unknown mode {effective_mode!r}")
        instance = get_app(effective_mode)
        if request.reset:
            instance.reset()
        turn = instance.handle_turn(request.message)
        return ChatResponse(
            mode=effective_mode,
            response=turn.response,
            turn=turn.to_dict(),
        )

    return app


app = create_app()
