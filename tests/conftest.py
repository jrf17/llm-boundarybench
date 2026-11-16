"""Pytest fixtures.

PyRIT is initialized once per session against an in-memory store so the
integration smoke test exercises a real PyRIT attack without any hosted model.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest


@pytest.fixture(scope="session")
def pyrit_ready() -> None:
    """Initialize PyRIT's in-memory store once for the whole session."""
    try:
        from pyrit.setup import initialize_pyrit_async
    except ImportError:
        pytest.skip("PyRIT not installed; install with `pip install 'boundarybench[pyrit]'`")

    asyncio.run(initialize_pyrit_async(memory_db_type="InMemory"))
    return None


@pytest.fixture()
def app_vulnerable() -> Any:
    from boundarybench.application.app import build_app

    return build_app("vulnerable")


@pytest.fixture()
def app_hardened() -> Any:
    from boundarybench.application.app import build_app

    return build_app("hardened")
