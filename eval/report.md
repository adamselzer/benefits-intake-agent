# Eval report — benefits-intake-agent

Extractor: **truth** (deterministic truth extractor, no API key). Cases: 30.

## Safety metrics (the point)

| Metric | Result |
|---|---|
| Wrongful wave-through rate (should-review cases routed clear-eligible) | 0% |
| Denials emitted (no-deny invariant; must be 0) | 0 |
| Conflict-detection recall | 100% |
| Recovery under injected failures (routed to human) | 100% |

## Quality metrics

| Metric | Result |
|---|---|
| Route accuracy vs labels | 100% |
| Screening decision accuracy | 100% |
| Extraction field accuracy (financial) | 100% |
| Mean latency per case | 0.023s |

The wrongful wave-through rate is the headline: a case that should reach a human must never be auto-cleared. Recovery rate shows the same property under injected document corruption. With the truth extractor these isolate the deterministic pipeline; run `--extractor vision` for real extraction accuracy.
