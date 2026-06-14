"""Extract node: pull structured fields (with confidence) from each document.

The extractor is injected so the graph can run with real Claude vision in
production and with a deterministic stand-in in tests/eval-without-key. The node
itself is thin; the uncertainty it produces is handled downstream.
"""

from __future__ import annotations

from typing import Any, Callable

from ..schema import ExtractedField

Extractor = Callable[[dict], list[ExtractedField]]


def make_extract_node(extractor: Extractor):
    def extract(state: dict[str, Any]) -> dict[str, Any]:
        fields: list[ExtractedField] = []
        for doc in state.get("documents", []):
            fields.extend(extractor(doc))
        return {"extracted": fields}

    return extract
