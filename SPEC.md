# Project 1 — `benefits-intake-agent`

**Pattern:** Agents / multi-step agentic workflow
**One line:** An agent that reads a messy benefits application plus uploaded verification documents,
extracts and validates the facts, screens the household across programs, and hands a caseworker a
recommendation packet — **without ever auto-denying anyone.**

This is the highest-demand, least-solved FDE pattern, and the safety-net framing is where it earns
its seat. The interview is won in the hard parts: what happens when extraction is wrong, how you
bound that error, and where you hand control back to deterministic code.

---

## Scope

**In scope**
- Ingest a synthetic application (structured JSON) + 2–4 synthetic uploaded documents per case
  (pay stub, lease, utility bill, ID).
- Extract structured fields from the documents (income, household members, address, dates).
- Normalize and cross-check extracted facts against the stated application (flag conflicts).
- Screen the household across 2–3 programs (SNAP + Medicaid is plenty; TANF optional) by calling the
  **rules-as-code core** (Project 4) rather than reasoning about eligibility in the model.
- Identify missing or insufficient verification documents.
- Produce a **caseworker recommendation packet**: eligibility screen results, confidence flags,
  missing-doc list, and every claim traced to its source document or rule.
- Route the case: clear-eligible / clear-ineligible / needs-human-review.

**Explicitly out of scope (state this in the README)**
- No final determinations. The agent recommends; a human decides.
- No auto-denial under any circumstances. Ambiguity routes to a human.
- No real applicant data, ever.

---

## The hard parts (where the interview is won)

Build these visibly, don't hide them:

1. **Extraction uncertainty.** Each extracted field carries a confidence. Low-confidence financial
   fields (income especially) never flow silently into a screen — they raise a flag or trigger
   human review.
2. **The deterministic handback.** The model extracts and reasons over messy inputs. The actual
   eligibility test is a tool call to deterministic, tested code (Project 4). Make the boundary
   explicit in the graph and narrate it in the README.
3. **Conflict detection.** Stated income on the application disagrees with the pay stub → the agent
   surfaces the conflict, it does not silently pick one.
4. **No-deny invariant.** Encode it structurally: there is no path in the graph that emits a denial.
   The worst outcome the agent can produce is "route to human."

---

## Architecture / repo structure

```
benefits-intake-agent/
├── README.md
├── data/
│   ├── generate_cases.py        # synthetic application + document generator
│   ├── cases/                   # generated synthetic cases (JSON + PDFs)
│   └── labels.json              # ground-truth screen outcome per case
├── src/
│   ├── graph.py                 # LangGraph state machine (the agent)
│   ├── nodes/
│   │   ├── ingest.py
│   │   ├── extract.py           # doc → structured fields + confidence
│   │   ├── validate.py          # normalize, cross-check, conflict detection
│   │   ├── screen.py            # calls rules-as-code (Project 4) per program
│   │   ├── verify_docs.py       # missing/insufficient verification logic
│   │   └── route.py             # eligible / ineligible / needs-review
│   ├── tools/                   # adapters to rules-as-code MCP + policy RAG
│   └── schema.py                # pydantic models for case, household, packet
├── app/                         # thin caseworker front-end (Streamlit or React)
├── eval/
│   ├── run_eval.py
│   ├── inject_failures.py       # corrupt docs, conflicting facts, OCR noise
│   └── report.md                # generated metrics + failure analysis
└── pyproject.toml
```

## Tech stack

- **LangGraph** for the stateful graph — it makes the deterministic/probabilistic boundary visible,
  which is exactly the story you want to tell. (Alternates worth a sentence in the README: OpenAI
  Agents SDK for handoffs/guardrails/tracing; smolagents if you want to show agent internals.)
- An extraction step over document images/PDFs (a vision-capable model, or OCR + a text model).
- The screening step calls **Project 4's rules-as-code core** (import it directly, or hit it as an
  MCP server — doing the latter shows composition).
- Thin front-end: Streamlit is fastest; a small React view is more impressive if time allows.

Cite Anthropic's *Building Effective AI Agents* in the README to show the design is deliberate, not
improvised.

---

## Synthetic data

`generate_cases.py` should produce, say, 50–100 cases spanning: clearly eligible, clearly ineligible,
near-threshold, missing-document, and conflicting-document scenarios. Generate the application JSON
programmatically; render the supporting docs as simple PDFs (a templated pay stub, lease, utility
bill) so the extraction step has something real to read. Store a ground-truth screen outcome per case
in `labels.json`. **Make the README loud about the fact that all data is synthetic and why.**

---

## Evaluation (the differentiator)

`eval/run_eval.py` runs the full set and reports:

- **Extraction field accuracy** per field type (income fields broken out — they matter most).
- **Screening decision accuracy** vs. ground truth.
- **Wrongful-denial rate** — the headline safety metric. By construction this should be **zero**
  (the agent can't deny), so frame it as: *of cases that should have been flagged for review, how
  many were instead waved through as clear-eligible?* That's the dangerous error, and that's the
  number to drive down.
- **Conflict-detection recall** on the conflicting-document cases.
- **Recovery rate** under injected failures (`inject_failures.py`): corrupt a pay stub, flip a
  number, add OCR noise — does the agent route to human instead of guessing?
- **Latency** per case and **cost** per case.

Report a before/after when you add confidence thresholds or the conflict-detection step.

---

## README framing

Lead with the stake: *a wrongful denial is a family losing food or medical coverage, so this agent is
built so that the worst thing it can do is ask a human to look.* Then walk through the graph and point
at the exact node where control leaves the model and enters deterministic code. Close with the eval
table.

## Interview one-liner

> "It never denies. It extracts, bounds its own uncertainty, and hands a caseworker a recommendation
> where every claim traces to a document or a rule. Here's the rate at which it waved through cases it
> should have flagged — and here's how the confidence thresholds drove it down."

## Build order for Claude Code

1. `schema.py` + `generate_cases.py` + `labels.json`.
2. `eval/run_eval.py` skeleton (so you're measuring from day one).
3. Extraction and validation nodes.
4. Screening via the rules core; routing; the no-deny invariant.
5. Failure injection + full eval run + `report.md`.
6. Thin front-end last.
