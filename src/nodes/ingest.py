"""Ingest node: validate the incoming application and initialize working state."""

from __future__ import annotations

from typing import Any

from ..schema import StatedApplication


def ingest(state: dict[str, Any]) -> dict[str, Any]:
    # Validate the stated application against its schema (raises on malformed input).
    StatedApplication(**state["application"])
    return {
        "extracted": [],
        "conflicts": [],
        "flags": [],
        "missing_documents": [],
    }
