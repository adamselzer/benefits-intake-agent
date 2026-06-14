"""Screen node: the deterministic handback.

The validated facts go to the rules-as-code core, which returns the cross-program
screen and the SNAP determination with its citations. The model does not decide
eligibility here; it has already done its job (extraction) and the determination is
made by tested, cited code.
"""

from __future__ import annotations

from typing import Any

from ..tools.rules_core import screen_household


def screen(state: dict[str, Any]) -> dict[str, Any]:
    result = screen_household(state["validated"])
    return {"screen": [result]}
