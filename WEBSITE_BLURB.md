# Website blurb: benefits-intake-agent

Drop-in copy for a portfolio page. A short paragraph plus highlight bullets.

---

## benefits-intake-agent

An agent that reads a messy benefits application and its verification documents,
cross-checks the facts, screens the household across programs, and hands a
caseworker a recommendation, without ever denying anyone. The design question this
project answers is the one that actually matters for AI in government: where does
the model stop and the auditable code start? Here the model reads the pay stub and
the lease and bounds its own uncertainty; the eligibility decision is a call into a
deterministic, cited rules core; and the worst outcome the agent can produce is
"route this to a human." It is the agents project in a four-part portfolio on AI in
the safety net, and it screens through the rules-as-code service built alongside it.

**Highlights**

- A LangGraph pipeline (extract, validate, screen, route) with the model confined
  to reading documents and the eligibility decision handed to deterministic code.
- A no-deny invariant enforced structurally: the route has no denial value, and any
  conflict, low-confidence financial field, or missing document forces human review.
- Extraction with per-field confidence; a low-confidence income figure never flows
  silently into a screen.
- Evaluated on the metric that maps to harm, the wrongful wave-through rate (cases
  that should have been reviewed but were auto-cleared): 0% with the deterministic
  pipeline, 0 denials, 100% conflict-detection recall and recovery under injected
  document corruption.
- Composes with the rules-as-code MCP server: every screen carries a determination,
  a rule trace, and a policy citation.

---

*Voice note: drafted in the plain, finding-first house style from your other
writing (no em dashes, evidence over decoration). Worth a pass against the live
aselzer.com voice before publishing.*
