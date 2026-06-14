"""Data models for the intake agent.

The shapes here encode the safety posture of the whole project:

- Extracted facts carry a per-field confidence, because a number read off a pay
  stub is not the same kind of fact as a number a caseworker typed.
- The route enum has no "denied" value. The worst outcome the agent can produce is
  NEEDS_HUMAN_REVIEW. That is the no-deny invariant, made structural.
- Every line in the recommendation packet carries provenance: a source document or
  a cited rule. Nothing in the packet is the model's unsourced opinion.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class DocType(str, Enum):
    PAY_STUB = "pay_stub"
    LEASE = "lease"
    UTILITY_BILL = "utility_bill"
    ID = "id"


class StatedMember(BaseModel):
    name: str
    age: int = Field(ge=0, le=130)
    disabled: bool = False


class StatedApplication(BaseModel):
    """What the applicant reported on the application form (may be wrong/incomplete)."""

    case_id: str
    members: list[StatedMember]
    stated_monthly_earned_income: float = Field(ge=0, default=0.0)
    stated_monthly_unearned_income: float = Field(ge=0, default=0.0)
    stated_monthly_rent: float = Field(ge=0, default=0.0)
    stated_monthly_utilities: float = Field(ge=0, default=0.0)
    address: str = ""


class Document(BaseModel):
    doc_type: DocType
    path: str
    # The true values the document encodes (used only to score extraction; the
    # agent never sees these).
    truth: dict[str, float | str] = Field(default_factory=dict)


class ExtractedField(BaseModel):
    name: str
    value: float | str | None
    confidence: float = Field(ge=0.0, le=1.0)
    source_doc: str
    note: str = ""


class Conflict(BaseModel):
    field: str
    stated_value: float | str
    extracted_value: float | str
    note: str = ""


class CaseRoute(str, Enum):
    CLEAR_ELIGIBLE = "clear_eligible"
    CLEAR_INELIGIBLE = "clear_ineligible"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    # Note: there is deliberately no DENIED route. See module docstring.


class ProvenancedClaim(BaseModel):
    claim: str
    basis: str  # "document: pay_stub" or "rule: 7 CFR 273.9(a)(2)"


class RecommendationPacket(BaseModel):
    case_id: str
    route: CaseRoute
    screen: list[dict] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    claims: list[ProvenancedClaim] = Field(default_factory=list)
    summary: str = ""

    def has_denial(self) -> bool:
        """Invariant probe: the packet must never represent a denial."""
        return self.route == "denied" or "deny" in self.summary.lower().split()
