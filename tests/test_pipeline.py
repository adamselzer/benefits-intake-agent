"""Deterministic tests for the agent pipeline (no API key needed).

These exercise the safety-critical logic with the truth extractor: conflict
detection, confidence bounding, the no-deny invariant, and the deterministic
handback to the rules core.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.graph import build_graph, load_case
from src.nodes.route import route
from src.nodes.validate import validate
from src.schema import CaseRoute, ExtractedField, RecommendationPacket
from src.tools.extraction import truth_extractor
from src.tools.rules_core import screen_household, to_household

CASES = Path(__file__).resolve().parent.parent / "data" / "cases"


# --- composition with the rules core ---------------------------------------


def test_rules_core_composition():
    facts = {"members": [{"age": 30}, {"age": 5}], "earned": 900, "unearned": 0, "rent": 800, "utilities": 200}
    result = screen_household(facts)
    assert result["snap_decision"] in {"eligible", "ineligible"}
    assert result["snap_citations"], "screen must carry citations from the rules core"
    assert any("SNAP" in s["program"] for s in result["screens"])


def test_to_household_builds_income():
    hh = to_household({"members": [{"age": 40}], "earned": 1000, "unearned": 200, "rent": 0, "utilities": 0})
    assert hh.earned_income == 1000 and hh.unearned_income == 200


# --- validate node ----------------------------------------------------------


def _state(app, extracted):
    return {"application": app, "extracted": extracted}


def test_validate_detects_conflict():
    app = {"members": [{"age": 30}], "stated_monthly_earned_income": 1000,
           "stated_monthly_rent": 0, "stated_monthly_utilities": 0, "stated_monthly_unearned_income": 0}
    extracted = [ExtractedField(name="monthly_earned_income", value=2500, confidence=0.95, source_doc="pay_stub")]
    out = validate(_state(app, extracted))
    assert out["conflicts"], "a 2.5x income disagreement must be flagged as a conflict"
    assert out["validated"]["earned"] == 2500  # prefers the document value


def test_validate_flags_low_confidence_income():
    app = {"members": [{"age": 30}], "stated_monthly_earned_income": 1000,
           "stated_monthly_rent": 0, "stated_monthly_utilities": 0, "stated_monthly_unearned_income": 0}
    extracted = [ExtractedField(name="monthly_earned_income", value=1000, confidence=0.4, source_doc="pay_stub")]
    out = validate(_state(app, extracted))
    assert any(f.startswith("low_confidence:monthly_earned_income") for f in out["flags"])


def test_validate_no_conflict_when_within_tolerance():
    app = {"members": [{"age": 30}], "stated_monthly_earned_income": 1000,
           "stated_monthly_rent": 0, "stated_monthly_utilities": 0, "stated_monthly_unearned_income": 0}
    extracted = [ExtractedField(name="monthly_earned_income", value=1020, confidence=0.95, source_doc="pay_stub")]
    out = validate(_state(app, extracted))
    assert not out["conflicts"]


# --- route node / no-deny invariant -----------------------------------------


def _screen_block(decision="eligible"):
    return {"snap_decision": decision, "snap_summary": "summary", "snap_citations": [{"label": "7 CFR 273.9"}], "screens": []}


def test_conflict_forces_human_review():
    state = {"case_id": "x", "validated": {"earned": 1}, "extracted": [],
             "conflicts": [{"field": "monthly_earned_income", "stated_value": 1000, "extracted_value": 2500}],
             "flags": [], "missing_documents": [], "screen": [_screen_block("eligible")]}
    out = route(state)
    assert out["route"] == CaseRoute.NEEDS_HUMAN_REVIEW.value


def test_low_confidence_forces_human_review():
    state = {"case_id": "x", "validated": {"earned": 1}, "extracted": [], "conflicts": [],
             "flags": ["low_confidence:monthly_earned_income (0.40)"], "missing_documents": [],
             "screen": [_screen_block("eligible")]}
    assert route(state)["route"] == CaseRoute.NEEDS_HUMAN_REVIEW.value


def test_missing_document_forces_human_review():
    state = {"case_id": "x", "validated": {"earned": 1}, "extracted": [], "conflicts": [], "flags": [],
             "missing_documents": ["pay_stub"], "screen": [_screen_block("eligible")]}
    assert route(state)["route"] == CaseRoute.NEEDS_HUMAN_REVIEW.value


def test_clean_eligible_case_routes_clear_eligible():
    state = {"case_id": "x", "validated": {"earned": 900}, "extracted": [], "conflicts": [], "flags": [],
             "missing_documents": [], "screen": [_screen_block("eligible")]}
    assert route(state)["route"] == CaseRoute.CLEAR_ELIGIBLE.value


def test_route_never_denies():
    # Across many shapes, the route enum has no denial and the packet probe agrees.
    for decision in ("eligible", "ineligible"):
        state = {"case_id": "x", "validated": {"earned": 900}, "extracted": [], "conflicts": [], "flags": [],
                 "missing_documents": [], "screen": [_screen_block(decision)]}
        out = route(state)
        packet = RecommendationPacket(**out["packet"])
        assert out["route"] != "denied"
        assert not packet.has_denial()


# --- end-to-end -------------------------------------------------------------


def test_graph_runs_end_to_end_and_never_denies():
    graph = build_graph(truth_extractor)
    routes = set()
    for cd in sorted(CASES.glob("case-*")):
        state = graph.invoke(load_case(cd))
        routes.add(state["route"])
        assert RecommendationPacket(**state["packet"])  # packet always assembles
    assert "denied" not in routes
    assert routes <= {"clear_eligible", "clear_ineligible", "needs_human_review"}
