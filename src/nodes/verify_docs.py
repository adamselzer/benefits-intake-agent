"""Verify-docs node: identify missing or insufficient verification documents.

A determination cannot be confirmed on facts that were never verified. This node
compares the documents actually provided against what the facts require, and lists
what is missing. A missing required document sends the case to a human.
"""

from __future__ import annotations

from typing import Any


def verify_docs(state: dict[str, Any]) -> dict[str, Any]:
    provided = {d["doc_type"] for d in state.get("documents", [])}
    facts = state["validated"]
    missing: list[str] = []

    if "id" not in provided:
        missing.append("id (identity verification)")
    if facts.get("earned", 0) > 0 and "pay_stub" not in provided:
        missing.append("pay_stub (earned income is claimed but unverified)")
    if facts.get("rent", 0) > 0 and "lease" not in provided:
        missing.append("lease (rent is claimed but unverified)")
    if facts.get("utilities", 0) > 0 and "utility_bill" not in provided:
        missing.append("utility_bill (utilities claimed but unverified)")

    return {"missing_documents": missing}
