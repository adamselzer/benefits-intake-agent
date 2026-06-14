"""Document extraction via Claude vision.

Each verification document is sent to Claude as a PDF document block, and the model
is asked to extract the relevant fields AND a calibrated confidence for each. The
confidence is load-bearing: a low-confidence financial field is never trusted
silently downstream (see the validate node), it routes the case to a human.

This is the probabilistic half of the pipeline. Its output is bounded and checked
by the deterministic half.
"""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import anthropic

from ..config import MODEL, anthropic_key
from ..schema import ExtractedField

_JSON = re.compile(r"\{.*\}", re.DOTALL)

# Which fields to pull from each document type, and how to name them.
DOC_FIELDS = {
    "pay_stub": ["monthly_earned_income"],
    "lease": ["monthly_rent"],
    "utility_bill": ["monthly_utilities"],
    "id": ["name", "age"],
}

SYSTEM = (
    "You extract structured facts from a single benefits verification document. "
    "Report only what the document shows. For every field, give a confidence in "
    "[0,1] reflecting how clearly the document supports the value. If a field is "
    "not present, use null with confidence 0."
)


def _client() -> anthropic.Anthropic:
    key = anthropic_key()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set; add it to .env for extraction.")
    return anthropic.Anthropic(api_key=key)


def extract_document(doc: dict, client: anthropic.Anthropic | None = None) -> list[ExtractedField]:
    doc_type = doc["doc_type"]
    fields = DOC_FIELDS.get(doc_type, [])
    client = client or _client()
    data = base64.standard_b64encode(Path(doc["path"]).read_bytes()).decode()
    schema_hint = ", ".join(f'"{f}"' for f in fields)
    prompt = (
        f"This is a {doc_type.replace('_', ' ')}. Extract these fields: {schema_hint}. "
        'Reply ONLY as JSON: {"fields": {"<name>": {"value": <number|string|null>, '
        '"confidence": <0..1>}}}. Monetary values must be monthly numbers without '
        "currency symbols or commas."
    )
    msg = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": [
                {"type": "document",
                 "source": {"type": "base64", "media_type": "application/pdf", "data": data}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    text = "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
    return _parse(text, doc_type, fields)


def truth_extractor(doc: dict) -> list[ExtractedField]:
    """A deterministic, no-LLM extractor that reads the document's known truth.

    Used to test the deterministic pipeline and to run the graph offline without an
    API key. It simulates a perfect, high-confidence vision extraction so the
    downstream validation/screening/routing logic can be exercised in isolation.
    """
    doc_type = doc["doc_type"]
    truth = doc.get("truth", {})
    name_map = {
        "monthly_earned_income": "monthly_earned_income",
        "monthly_rent": "monthly_rent",
        "monthly_utilities": "monthly_utilities",
        "name": "name",
        "age": "age",
    }
    out: list[ExtractedField] = []
    for f in DOC_FIELDS.get(doc_type, []):
        key = name_map.get(f, f)
        if key in truth:
            out.append(ExtractedField(name=f, value=truth[key], confidence=0.99, source_doc=doc_type))
    return out


def _parse(text: str, doc_type: str, fields: list[str]) -> list[ExtractedField]:
    m = _JSON.search(text)
    data = json.loads(m.group(0)).get("fields", {}) if m else {}
    out: list[ExtractedField] = []
    for f in fields:
        entry = data.get(f, {}) if isinstance(data, dict) else {}
        value = entry.get("value") if isinstance(entry, dict) else None
        conf = float(entry.get("confidence", 0.0)) if isinstance(entry, dict) else 0.0
        if isinstance(value, str) and f != "name":
            # coerce numeric strings for money/age fields
            try:
                value = float(re.sub(r"[^0-9.]", "", value))
            except ValueError:
                pass
        out.append(ExtractedField(name=f, value=value, confidence=conf, source_doc=doc_type))
    return out
