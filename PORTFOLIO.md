# Portfolio notes: benefits-intake-agent

A plain-language account of what this project is and the judgment behind it.

## Pattern

**Agents / multi-step agentic workflow.** A stateful LangGraph pipeline that reads
documents, reasons over messy facts, and routes a case, with a deterministic core
making the actual decision.

## Concept demonstrated

Agentic workflow design with bounded uncertainty and human-in-the-loop safety:
knowing exactly where to hand control back from the model to deterministic code,
and building the graph so the dangerous outcome is structurally impossible. The
model does what it is good at (reading a messy pay stub); the eligibility decision
is a tested, cited rule call; and the worst thing the agent can do is ask a human
to look.

## Why it matters in this domain

This is the highest-demand, least-solved pattern in applied AI, and the safety-net
framing is where it earns its seat. An intake agent that auto-denies on a misread
number does real harm, so productivity is never the first concern. The questions
that matter are what happens when extraction is wrong, how you bound that error, and
where you hand control back to code. The whole design is an answer to those.

## Key design decisions and tradeoffs

1. **The no-deny invariant is structural.** The route enum has no
   denial value, and a test asserts none is ever produced. *Rejected:* a prompt
   instruction telling the model not to deny. Prompts drift; a type and a test do
   not. The worst outcome is `needs_human_review`.

2. **Per-field confidence that gates the screen.** Extraction returns a confidence
   per field, and a low-confidence financial field forces human review. *Rejected:*
   trusting extraction and screening on whatever the model returned. In this domain
   a confidently-wrong income figure is the failure mode, so uncertainty has to be a
   first-class signal that can stop the screen.

3. **The eligibility test is a deterministic tool call.** The
   screen node calls the rules-as-code core. *Rejected:* letting the model reason
   about eligibility from the policy. The model orchestrates; auditable code
   decides. This is the single most important boundary in the project, and it is a
   named node in the graph.

4. **Conflicts are surfaced and routed to a human.** When a document disagrees with the
   application, the agent reports both and routes to a human. *Rejected:* having the
   model pick the "more likely" value. Silently choosing is exactly how a wrongful
   determination happens.

5. **An injectable extractor.** The graph takes the extractor as a dependency: Claude
   vision in production, a deterministic stand-in for tests and offline runs.
   *Rejected:* hard-wiring the LLM call into the node. Injection makes the entire
   pipeline testable without a key and lets the safety logic be verified
   deterministically.

## How it's evaluated

The harness reports safety metrics first, then quality metrics. The headline is the
**wrongful wave-through rate**: of the cases that should have reached a human, how
many were instead auto-cleared? Because the agent cannot deny, that is the dangerous
error. With the deterministic extractor (which isolates the routing logic) it is 0%,
denials are 0, conflict-detection recall is 100%, and recovery under injected pay-
stub corruption is 100%. The real Claude-vision run adds extraction field accuracy
and the realistic wave-through rate under genuine model error.

These metrics were chosen because they map to harm. A wave-through is a family that
should have been reviewed and was not; a denial is something the agent must never
do; a missed conflict is a wrong determination waiting to happen.

## What I'd do differently at production scale

- Tune extraction prompts and confidence thresholds on real (photographed, skewed,
  partial) document distributions, and calibrate the model's self-reported
  confidence against measured error.
- Build the review queue, audit log, and feedback loop around the recommendation
  packet.
- Move the screen step from a direct import to the MCP client so the rules core
  versions and deploys independently.
