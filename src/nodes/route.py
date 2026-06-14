"""Route node: the bounded decision and the recommendation packet.

The no-deny invariant is structural here. The route is one of three values, none of
which is a denial; the worst outcome the agent can produce is NEEDS_HUMAN_REVIEW.
Any conflict, any low-confidence financial field, or any missing required document
forces review. Only a clean case with a determinate screen is routed as
clear-eligible or clear-ineligible, and even those are recommendations a human
confirms.
"""

from __future__ import annotations

from typing import Any

from ..schema import (
    CaseRoute,
    Conflict,
    ProvenancedClaim,
    RecommendationPacket,
)

ALLOWED_ROUTES = {CaseRoute.CLEAR_ELIGIBLE, CaseRoute.CLEAR_INELIGIBLE, CaseRoute.NEEDS_HUMAN_REVIEW}

FIELD_LABEL = {
    "earned": "monthly earned income",
    "rent": "monthly rent",
    "utilities": "monthly utilities",
}


def route(state: dict[str, Any]) -> dict[str, Any]:
    conflicts = [c if isinstance(c, Conflict) else Conflict(**c) for c in state.get("conflicts", [])]
    flags = state.get("flags", [])
    missing = state.get("missing_documents", [])
    screen = state["screen"][0]
    extracted_fields = {f.name for f in state.get("extracted", [])}

    low_conf = [f for f in flags if f.startswith("low_confidence")]
    needs_review = bool(conflicts) or bool(missing) or bool(low_conf)

    if needs_review:
        decision = CaseRoute.NEEDS_HUMAN_REVIEW
    elif screen["snap_decision"] == "eligible":
        decision = CaseRoute.CLEAR_ELIGIBLE
    else:
        decision = CaseRoute.CLEAR_INELIGIBLE

    # The invariant, asserted: no denial path exists.
    assert decision in ALLOWED_ROUTES, "route must never be a denial"

    # Provenanced claims: every fact traces to a document or a cited rule.
    claims: list[ProvenancedClaim] = []
    facts = state["validated"]
    doc_field_present = {
        "earned": "monthly_earned_income" in extracted_fields,
        "rent": "monthly_rent" in extracted_fields,
        "utilities": "monthly_utilities" in extracted_fields,
    }
    for key, label in FIELD_LABEL.items():
        if key in facts:
            basis = "document" if doc_field_present.get(key) else "application (stated, unverified)"
            claims.append(ProvenancedClaim(claim=f"{label} = ${float(facts[key]):,.0f}", basis=basis))
    citation = screen["snap_citations"][0]["label"] if screen.get("snap_citations") else "rules-as-code"
    claims.append(ProvenancedClaim(claim=screen["snap_summary"], basis=f"rule: {citation}"))

    summary = _summary(decision, screen, conflicts, missing, low_conf)
    packet = RecommendationPacket(
        case_id=state["case_id"],
        route=decision,
        screen=screen["screens"],
        flags=flags,
        missing_documents=missing,
        conflicts=conflicts,
        claims=claims,
        summary=summary,
    )
    return {"route": decision.value, "packet": packet.model_dump()}


def _summary(decision, screen, conflicts, missing, low_conf) -> str:
    if decision == CaseRoute.NEEDS_HUMAN_REVIEW:
        reasons = []
        if conflicts:
            reasons.append(f"{len(conflicts)} document/application conflict(s)")
        if missing:
            reasons.append(f"{len(missing)} missing verification(s)")
        if low_conf:
            reasons.append(f"{len(low_conf)} low-confidence financial field(s)")
        return "Routed to human review: " + "; ".join(reasons) + ". The agent does not decide; a caseworker will."
    verb = "appears eligible" if decision == CaseRoute.CLEAR_ELIGIBLE else "appears ineligible"
    return (
        f"Recommendation only: the household {verb} for SNAP per the rules core "
        f"({screen['snap_summary']}). A caseworker confirms the determination."
    )
