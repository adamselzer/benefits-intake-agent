# benefits-intake-agent

An agent that reads a messy benefits application and its verification documents,
extracts and cross-checks the facts, screens the household across programs by
calling a deterministic rules core, and hands a caseworker a recommendation
packet. **It never denies anyone.** The worst outcome it can produce is "route
this to a human."

This is the agents project in a four-part portfolio on AI in the public benefits
safety net. It composes with the other repos: it screens via `rules-as-code-mcp`
and is the consumer the rules core was built to serve.

> A wrongful denial is a family losing food or medical coverage. So this agent is
> built so that the worst thing it can do is ask a human to look. The model reads
> and reasons over messy inputs; the eligibility decision is made by deterministic,
> cited code; and there is no path through the graph that emits a denial.

## The graph

```
ingest -> extract -> validate -> screen -> verify_docs -> route
```

- **ingest** validates the application against its schema.
- **extract** (the model) reads each document with Claude vision and returns
  structured fields, each with a confidence.
- **validate** normalizes the facts, cross-checks documents against the stated
  application, surfaces conflicts, and flags low-confidence financial fields.
- **screen** is the deterministic handback: it calls the `rules-as-code-mcp` core,
  which returns a SNAP determination with a rule trace and a policy citation. The
  model does not decide eligibility.
- **verify_docs** lists missing or insufficient verification documents.
- **route** emits one of three outcomes, none of which is a denial.

The design follows Anthropic's [Building Effective AI Agents](https://www.anthropic.com/research/building-effective-agents):
a small, inspectable graph with the model confined to the step it is genuinely good
at (reading messy documents) and control handed back to deterministic code for the
decision.

## The hard parts (built visibly, not hidden)

1. **Extraction uncertainty.** Every extracted field carries a confidence. A
   low-confidence financial field never flows silently into a screen; it raises a
   flag and forces human review.
2. **The deterministic handback.** The eligibility test is a call into tested,
   cited code, not model judgment. The boundary is a named node in the graph.
3. **Conflict detection.** When the stated income disagrees with the pay stub, the
   agent surfaces the conflict instead of silently picking one.
4. **The no-deny invariant.** Structural: the route enum has no denial value, and a
   test asserts no case ever produces one. Conflicts, low-confidence financials, and
   missing documents all force `needs_human_review`.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pip install -e ../rules-as-code-mcp     # the deterministic rules core (sibling repo)

python data/generate_cases.py           # 30 synthetic cases with rendered PDFs
python eval/run_eval.py                  # offline eval (deterministic extractor, no key)
pytest                                   # 11 tests

# Optional, with a key:
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
python eval/run_eval.py --extractor vision   # real Claude-vision extraction
python clients/mcp_compose_demo.py           # screen via the rules core over MCP
streamlit run app/app.py                     # caseworker UI
```

## Synthetic data only, never real PII

`data/generate_cases.py` produces 30 cases spanning clearly-eligible,
clearly-ineligible, near-threshold, missing-document, and conflicting-document
scenarios. Each case is a stated application plus rendered PDF documents (pay stub,
lease, utility bill, ID) with a ground-truth label. All synthetic. Handling
applicant data correctly is a core public-sector competency, so the pipeline is
built to run on synthetic cases and never touches real PII.

## Evaluation

Evaluation is the deliverable. The harness reports safety metrics first.

Run with the **deterministic truth extractor** (isolates the pipeline logic, no API
key, fully reproducible):

| Metric | Result |
|---|---|
| Wrongful wave-through rate (should-review cases routed clear-eligible) | **0%** |
| Denials emitted (no-deny invariant) | **0** |
| Conflict-detection recall | **100%** |
| Recovery under injected failures (routed to human) | **100%** |
| Route accuracy vs labels | 100% |
| Screening decision accuracy | 100% |
| Mean latency per case | 0.02s |

The **wrongful wave-through rate** is the headline. Because the agent cannot deny,
the dangerous error is the opposite one: waving through a case that should have been
flagged. The truth-extractor run drives it to zero by construction of the routing
logic; the failure-injection test corrupts a pay stub and confirms the agent
escalates rather than guesses.

`python eval/run_eval.py --extractor vision` runs the same harness with real Claude
vision extraction, which adds extraction field accuracy and exercises the
uncertainty handling under genuine model error. That run requires a key and is the
one to watch for the realistic wave-through rate.

## Composition

The screen step imports the `rules-as-code-mcp` core directly for reliability, and
`clients/mcp_compose_demo.py` demonstrates the deployable shape: the same screen
performed by calling that project's MCP server over stdio, returning a determination
with its rule trace and citations. See `clients/compose_transcript.md`.

## What I'd do differently at production scale

- **Real document variety.** The synthetic PDFs are clean; production documents are
  photographed, skewed, and partial. The confidence-and-escalate machinery is built
  for that, but the extraction prompts and thresholds would need tuning on real
  document distributions.
- **Human-in-the-loop UI and audit.** The recommendation packet is the artifact a
  caseworker acts on; production needs the review queue, the audit log, and the
  feedback loop that retrains thresholds.
- **Calibrated confidence.** The per-field confidence is the model's self-report;
  at scale I would calibrate it against measured extraction error.
- **MCP in the hot path.** Move the screen step from direct import to the MCP client
  so the rules core can be versioned and deployed independently.
