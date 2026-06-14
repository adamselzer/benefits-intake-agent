"""Configuration and key loading."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parent.parent
load_dotenv(REPO / ".env")

MODEL = os.environ.get("INTAKE_MODEL", "claude-sonnet-4-6")

# A financial field extracted below this confidence never flows silently into a
# screen; it raises a flag and routes the case to a human.
LOW_CONFIDENCE_THRESHOLD = float(os.environ.get("LOW_CONFIDENCE_THRESHOLD", "0.75"))

# Relative gap between a stated value and an extracted value that counts as a
# conflict to surface (10%).
CONFLICT_TOLERANCE = float(os.environ.get("CONFLICT_TOLERANCE", "0.10"))


def anthropic_key() -> str | None:
    return os.environ.get("ANTHROPIC_API_KEY", "").strip() or None


def has_llm() -> bool:
    return anthropic_key() is not None
