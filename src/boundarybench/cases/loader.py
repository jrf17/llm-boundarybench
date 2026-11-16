"""Test-case schema (JSON Schema) and loader.

Test cases are versioned JSON documents validated against this schema. The
schema is deliberately strict so a malformed case fails at load time instead of
silently producing a meaningless run.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

SCHEMA_VERSION = "1.0"

TEST_CASE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "BoundaryBench test case",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "id",
        "name",
        "category",
        "threat_objective",
        "input_surface",
        "trust_boundary",
        "turns",
        "expected_authorized",
        "expected_vulnerable",
        "expected_hardened",
        "scoring",
        "required_evidence",
    ],
    "properties": {
        "id": {"type": "string", "pattern": "^[A-Za-z0-9_\\-]+$"},
        "name": {"type": "string", "minLength": 1},
        "category": {
            "type": "string",
            "enum": [
                "direct_injection",
                "retrieval_injection",
                "tool_output",
                "multi_turn",
                "information_disclosure",
                "benign",
            ],
        },
        "threat_objective": {"type": "string", "minLength": 1},
        "input_surface": {
            "type": "string",
            "enum": ["user_prompt", "retrieved_document", "tool_output", "conversation"],
        },
        "trust_boundary": {"type": "string", "minLength": 1},
        "payload": {"type": "string"},
        "fixture": {"type": "string"},
        "turns": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1},
        },
        "expected_authorized": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "action": {"type": "string"},
                "tool": {"type": ["string", "null"]},
            },
        },
        "expected_vulnerable": {"type": "string", "enum": ["violation", "no_violation"]},
        "expected_hardened": {"type": "string", "enum": ["violation", "no_violation"]},
        "scoring": {
            "type": "object",
            "additionalProperties": False,
            "required": ["violation_type"],
            "properties": {
                "violation_type": {
                    "type": "string",
                    "enum": [
                        "unauthorized_tool",
                        "disclosure",
                        "injection_followed",
                        "exfiltration",
                    ],
                },
                "marker": {"type": "string"},
                "tool": {"type": "string"},
                "forbidden_source": {
                    "type": "string",
                    "enum": ["retrieved", "tool_output", "system", "user"],
                },
                "detail": {"type": "string"},
            },
        },
        "required_evidence": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}


class CaseValidationError(ValueError):
    """Raised when a test case does not conform to the schema."""


class CaseLoader:
    """Loads and validates test-case documents from a directory tree."""

    def __init__(self, schema: dict[str, Any] | None = None) -> None:
        self.schema = schema or TEST_CASE_SCHEMA
        self._validator = jsonschema.Draft202012Validator(self.schema)

    def load_file(self, path: Path) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CaseValidationError(f"{path}: invalid JSON: {exc}") from exc

        errors = sorted(self._validator.iter_errors(data), key=lambda e: list(e.path))
        if errors:
            lines = [f"{path}: {e.message} (at {list(e.path)})" for e in errors]
            raise CaseValidationError("\n".join(lines))

        return data

    def load_dir(self, directory: Path) -> list[dict[str, Any]]:
        cases: list[dict[str, Any]] = []
        for path in sorted(directory.rglob("*.json")):
            cases.append(self.load_file(path))
        return cases

    def load_all(self, directories: list[Path]) -> list[dict[str, Any]]:
        cases: list[dict[str, Any]] = []
        for directory in directories:
            if directory.is_dir():
                cases.extend(self.load_dir(directory))
        return cases
