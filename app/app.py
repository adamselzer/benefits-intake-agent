"""Streamlit caseworker view of the intake agent.

Pick a synthetic case, run the agent, and read the recommendation packet: the
route, the flags, the conflicts and missing documents that drove it, and every
claim with its provenance (a source document or a cited rule). The point the UI
makes visible: the agent recommends and traces its reasoning; it never decides.

Runs with the deterministic truth extractor by default; with ANTHROPIC_API_KEY set,
you can switch to real Claude-vision extraction.

Run:  streamlit run app/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from app._ui import apply_theme, footer, header
from src.config import has_llm
from src.graph import build_graph, default_extractor, load_case
from src.tools.extraction import truth_extractor

CASES = Path(__file__).resolve().parent.parent / "data" / "cases"

ROUTE_STYLE = {
    "clear_eligible": ("✅ Clear — eligible (recommendation)", "success"),
    "clear_ineligible": ("⛔ Clear — ineligible (recommendation)", "warning"),
    "needs_human_review": ("🧑‍⚖️ Needs human review", "info"),
}

st.set_page_config(page_title="Benefits intake agent", layout="wide")
apply_theme(st)
header(
    st,
    "Intake triage · food assistance",
    "Benefits intake agent",
    "The agent reads the application and verification documents, screens via a "
    "deterministic rules core, and hands a caseworker a recommendation. It never "
    "denies, and never auto-clears a case that should be reviewed.",
)

case_dirs = sorted(p.name for p in CASES.glob("case-*"))
if not case_dirs:
    st.error("No cases found. Run `python data/generate_cases.py` first.")
    st.stop()

with st.sidebar:
    st.header("Run settings")
    use_vision = False
    if has_llm():
        use_vision = st.checkbox("Use Claude vision extraction", value=False,
                                 help="Off = deterministic truth extractor (free, instant).")
    else:
        st.warning("No ANTHROPIC_API_KEY: deterministic extractor only.")
    case_name = st.selectbox("Case", case_dirs)

extractor = default_extractor() if use_vision else truth_extractor

if st.button("Run intake agent", type="primary"):
    with st.spinner("Running the agent graph..."):
        state = build_graph(extractor).invoke(load_case(CASES / case_name))
    packet = state["packet"]

    label, kind = ROUTE_STYLE.get(packet["route"], (packet["route"], "info"))
    getattr(st, kind)(f"**Route: {label}**")
    st.write(packet["summary"])

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Flags")
        st.write(packet["flags"] or "_none_")
        st.subheader("Missing documents")
        st.write(packet["missing_documents"] or "_none_")
        st.subheader("Conflicts")
        if packet["conflicts"]:
            for cf in packet["conflicts"]:
                st.write(f"- **{cf['field']}**: stated ${cf['stated_value']:,.0f} vs document ${cf['extracted_value']:,.0f}")
        else:
            st.write("_none_")
    with c2:
        st.subheader("Claims (every claim traces to a source)")
        for claim in packet["claims"]:
            st.markdown(f"- {claim['claim']}  \n  _basis: {claim['basis']}_")

    st.subheader("Program screen (from the rules core)")
    st.json(packet["screen"])

footer(st, "Synthetic cases, no PII · the agent recommends, a caseworker decides")
