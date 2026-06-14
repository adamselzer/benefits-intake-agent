"""Validate node: normalize extracted facts, cross-check against the application,
detect conflicts, and bound extraction uncertainty.

Three safety behaviors live here:
  - Conflict detection: a document value that disagrees with the stated application
    by more than a tolerance is surfaced, never silently reconciled.
  - Confidence bounding: a low-confidence financial field raises a flag (and, via
    the route node, sends the case to a human) rather than flowing into the screen.
  - Document values are preferred over stated values for the screen, because the
    verification document is the more authoritative source.
"""

from __future__ import annotations

from typing import Any

from ..config import CONFLICT_TOLERANCE, LOW_CONFIDENCE_THRESHOLD
from ..schema import Conflict, ExtractedField

FINANCIAL = {"monthly_earned_income", "monthly_rent", "monthly_utilities"}
# extracted field name -> (stated application key, validated facts key)
FIELD_MAP = {
    "monthly_earned_income": ("stated_monthly_earned_income", "earned"),
    "monthly_rent": ("stated_monthly_rent", "rent"),
    "monthly_utilities": ("stated_monthly_utilities", "utilities"),
}


def _by_name(extracted: list[ExtractedField]) -> dict[str, ExtractedField]:
    return {f.name: f for f in extracted}


def validate(state: dict[str, Any]) -> dict[str, Any]:
    stated = state["application"]
    extracted = _by_name(state.get("extracted", []))
    conflicts: list[Conflict] = []
    flags: list[str] = []

    validated: dict[str, Any] = {
        "members": [{"age": m["age"], "disabled": m.get("disabled", False)} for m in stated["members"]],
        "unearned": float(stated.get("stated_monthly_unearned_income", 0.0)),
    }

    for field, (stated_key, facts_key) in FIELD_MAP.items():
        stated_val = float(stated.get(stated_key, 0.0))
        ef = extracted.get(field)
        if ef is not None and isinstance(ef.value, (int, float)):
            doc_val = float(ef.value)
            validated[facts_key] = doc_val  # prefer the document
            # conflict vs the stated application
            denom = max(abs(stated_val), 1.0)
            if abs(doc_val - stated_val) / denom > CONFLICT_TOLERANCE:
                conflicts.append(Conflict(
                    field=field, stated_value=stated_val, extracted_value=doc_val,
                    note="Document disagrees with the stated application.",
                ))
            if field in FINANCIAL and ef.confidence < LOW_CONFIDENCE_THRESHOLD:
                flags.append(f"low_confidence:{field} ({ef.confidence:.2f})")
        else:
            # no document value: fall back to the stated figure
            validated[facts_key] = stated_val

    return {"validated": validated, "conflicts": conflicts, "flags": flags}
