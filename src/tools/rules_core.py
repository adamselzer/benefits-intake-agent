"""The deterministic handback: screening via the rules-as-code core.

This is the boundary the whole project is about. The model extracts and reasons
over messy documents; the eligibility screen itself is a call into the
rules-as-code-mcp project's deterministic core, which returns a determination with
a rule trace and a policy citation. The agent never decides eligibility.

The core is imported directly here (the rules-as-code-mcp package is installed).
clients/mcp_compose_demo.py demonstrates the same screen performed over MCP, which
is the deployable shape: the agent reaching the deterministic core as an MCP tool.
"""

from __future__ import annotations

from typing import Any

from rules import (
    Household,
    IncomeSource,
    Person,
    determine_snap_eligibility,
    required_verifications,
    screen_programs,
)


def to_household(facts: dict[str, Any]) -> Household:
    """Build a rules-core Household from validated, normalized facts."""
    income = []
    if facts.get("earned"):
        income.append(IncomeSource(kind="earned", monthly_amount=float(facts["earned"])))
    if facts.get("unearned"):
        income.append(IncomeSource(kind="unearned", monthly_amount=float(facts["unearned"])))
    return Household(
        members=[Person(age=int(m["age"]), disabled=bool(m.get("disabled", False)))
                 for m in facts["members"]],
        income=income,
        shelter_cost_monthly=float(facts.get("rent", 0.0)),
        utilities_monthly=float(facts.get("utilities", 0.0)),
    )


def screen_household(facts: dict[str, Any]) -> dict[str, Any]:
    """Return the cross-program screen plus the SNAP determination and the
    verifications the rules core says are required. Pure and deterministic."""
    hh = to_household(facts)
    screens = [s.model_dump() for s in screen_programs(hh)]
    determination = determine_snap_eligibility(hh)
    verifications = [v.model_dump() for v in required_verifications("SNAP", hh)]
    return {
        "screens": screens,
        "snap_decision": determination.decision,
        "snap_summary": determination.summary,
        "snap_citations": determination.citations,
        "ruleset_version": determination.ruleset_version,
        "required_verifications": verifications,
    }
