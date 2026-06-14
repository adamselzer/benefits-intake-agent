"""The LangGraph state object threaded through the agent.

State is a TypedDict; each node returns a partial update. The fields make the
deterministic/probabilistic boundary legible: `extracted`/`conflicts` are what the
model produced, `screen` is what the deterministic rules core returned, and `route`
is the bounded decision.
"""

from __future__ import annotations

from typing import Any, TypedDict

from .schema import Conflict, ExtractedField


class AgentState(TypedDict, total=False):
    case_id: str
    application: dict[str, Any]  # the stated application (StatedApplication dump)
    documents: list[dict[str, Any]]  # [{doc_type, path, truth}]

    extracted: list[ExtractedField]  # model output, per-field confidence
    validated: dict[str, Any]  # normalized facts used for screening
    conflicts: list[Conflict]
    flags: list[str]

    screen: list[dict[str, Any]]  # program screen results from the rules core
    missing_documents: list[str]

    route: str  # CaseRoute value
    packet: dict[str, Any]  # RecommendationPacket dump
