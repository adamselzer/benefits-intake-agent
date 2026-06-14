"""The agent graph.

A LangGraph state machine that makes the deterministic/probabilistic boundary
explicit: `extract` (the model, over document images) feeds `validate`, and only
then does `screen` hand the determination to the deterministic rules core. The
`route` node emits one of three outcomes, none of which is a denial.

    ingest -> extract -> validate -> screen -> verify_docs -> route

The design follows Anthropic's "Building Effective AI Agents": a small, inspectable
graph with the model confined to the step it is actually good at (reading messy
documents), and control handed back to deterministic code for the decision.

The extractor is injected. In production it is Claude vision; for tests and
offline runs it is the deterministic truth_extractor.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from langgraph.graph import END, START, StateGraph

from .nodes.extract import make_extract_node
from .nodes.ingest import ingest
from .nodes.route import route
from .nodes.screen import screen
from .nodes.validate import validate
from .nodes.verify_docs import verify_docs
from .schema import ExtractedField
from .state import AgentState

Extractor = Callable[[dict], list[ExtractedField]]


def build_graph(extractor: Extractor):
    g = StateGraph(AgentState)
    g.add_node("ingest", ingest)
    g.add_node("extract", make_extract_node(extractor))
    g.add_node("validate", validate)
    g.add_node("screen", screen)
    g.add_node("verify_docs", verify_docs)
    g.add_node("route", route)

    g.add_edge(START, "ingest")
    g.add_edge("ingest", "extract")
    g.add_edge("extract", "validate")
    g.add_edge("validate", "screen")
    g.add_edge("screen", "verify_docs")
    g.add_edge("verify_docs", "route")
    g.add_edge("route", END)
    return g.compile()


def default_extractor() -> Extractor:
    """The production extractor: Claude vision, with one shared client."""
    import anthropic

    from .config import anthropic_key
    from .tools.extraction import extract_document

    client = anthropic.Anthropic(api_key=anthropic_key())
    return lambda doc: extract_document(doc, client=client)


def load_case(case_dir: str | Path) -> dict[str, Any]:
    case_dir = Path(case_dir)
    application = json.loads((case_dir / "application.json").read_text())
    documents = json.loads((case_dir / "documents.json").read_text())
    return {"case_id": application["case_id"], "application": application, "documents": documents}


def run_case(case_dir: str | Path, extractor: Extractor) -> dict[str, Any]:
    """Run the agent over one case directory and return the final state."""
    graph = build_graph(extractor)
    return graph.invoke(load_case(case_dir))
