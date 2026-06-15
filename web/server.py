"""A small FastAPI backend serving the bespoke caseworker front-end.

This is the hero surface for the suite: a hand-built interface (web/static) over
the real agent graph, where the deterministic/probabilistic boundary, per-field
confidence, and provenance are designed as first-class elements rather than
rendered by a framework's defaults.

Run:  uvicorn web.server:app --port 8600
      (from the repo root, with the venv active)
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.config import has_llm
from src.graph import build_graph, default_extractor, load_case
from src.tools.extraction import truth_extractor

WEB = Path(__file__).resolve().parent
CASES = WEB.parent / "data" / "cases"

app = FastAPI(title="benefits-intake-agent")


@app.get("/civil")
def civil_showcase() -> FileResponse:
    """The Civil design system showcase page."""
    return FileResponse(WEB / "static" / "civil.html")


@app.get("/api/cases")
def list_cases() -> list[dict]:
    labels = json.loads((CASES / "labels.json").read_text())["cases"]
    return [
        {"id": c["case_id"], "scenario": c["scenario"], "route": c["expected_route"]}
        for c in labels
    ]


@app.get("/api/status")
def status() -> dict:
    return {"vision_available": has_llm()}


@app.post("/api/run")
def run(payload: dict) -> dict:
    case_id = payload.get("case_id")
    vision = bool(payload.get("vision", False))
    if not case_id or not (CASES / case_id).exists():
        raise HTTPException(status_code=404, detail=f"Unknown case: {case_id}")
    if vision and not has_llm():
        raise HTTPException(status_code=400, detail="Vision needs ANTHROPIC_API_KEY in .env")

    extractor = default_extractor() if vision else truth_extractor
    state = build_graph(extractor).invoke(load_case(CASES / case_id))
    packet = state["packet"]
    return {
        "case_id": case_id,
        "extractor": "vision" if vision else "deterministic",
        "route": state["route"],
        "summary": packet["summary"],
        "extracted": [e.model_dump() for e in state.get("extracted", [])],
        "validated": state.get("validated", {}),
        "conflicts": packet["conflicts"],
        "flags": packet["flags"],
        "missing_documents": packet["missing_documents"],
        "claims": packet["claims"],
        # state["screen"][0] is the full rules-core result (decision, computed,
        # citations, ruleset); packet["screen"] is only the program-screen list.
        "screen": state["screen"][0] if state.get("screen") else {},
        "household_size": len(state["validated"]["members"]),
    }


# Static front-end (served at /). Registered last so /api/* wins.
app.mount("/", StaticFiles(directory=WEB / "static", html=True), name="static")
