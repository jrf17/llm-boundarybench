"""Deterministic retrieval workflow.

The synthetic application has a small in-memory document corpus. Retrieval is a
transparent, deterministic matcher: a query selects a document when it names
the document's ``doc_id``. This keeps the retrieval boundary real — attacker
content genuinely arrives via the document corpus, not via the user prompt —
while remaining fully reproducible offline and free of accidental matches
between benign queries and attacker-controlled content.

The corpus is small and keyed by document id by design. A token-overlap ranker
would introduce the very ambiguity this project is built to eliminate: a benign
query ("email the weekly report") sharing common words with an attacker document
would silently leak injected content into an unrelated evaluation.
"""

from __future__ import annotations

import re
from typing import Any

from boundarybench.config import AppConfig
from boundarybench.models import RetrievalResult

_ID_RE = re.compile(r"\b(kb-\d{3})\b", re.IGNORECASE)


def retrieve(query: str, config: AppConfig, top_k: int = 1) -> RetrievalResult:
    """Return the document(s) whose ``doc_id`` is named in ``query``."""
    corpus = list(config.retrieval_documents)
    explicit_ids = [m.lower() for m in _ID_RE.findall(query)]

    docs: list[dict[str, Any]] = []
    for doc in corpus:
        if doc.doc_id.lower() in explicit_ids:
            docs.append({"doc_id": doc.doc_id, "content": doc.content, "trusted": doc.trusted})

    return RetrievalResult(query=query, documents=docs[:top_k])
