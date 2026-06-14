"""Failure injection: corrupt a clean case and check the agent recovers.

Recovery means routing to a human, not guessing. A robust intake agent, handed a
pay stub whose number has been flipped or garbled, must notice that the document
disagrees with the application and escalate rather than wave the case through.
"""

from __future__ import annotations

import copy


def corrupt_pay_stub(case: dict) -> dict:
    """Flip the pay stub's income to a wrong value, simulating an OCR/data error.

    The corrupted document value will disagree with the stated application, which
    the validate node must catch as a conflict (-> human review)."""
    case = copy.deepcopy(case)
    for d in case["documents"]:
        if d["doc_type"] == "pay_stub" and "monthly_earned_income" in d.get("truth", {}):
            original = d["truth"]["monthly_earned_income"]
            d["truth"]["monthly_earned_income"] = round(original * 1.9) + 813
            d["_corrupted"] = True
    case["_injected_failure"] = "corrupted_pay_stub"
    return case
