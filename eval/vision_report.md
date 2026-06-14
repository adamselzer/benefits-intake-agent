# Eval report — benefits-intake-agent (real Claude vision extraction)

Captured from `python eval/run_eval.py --extractor vision` over all 30 cases. This
is the real-extraction complement to `report.md` (which isolates the deterministic
pipeline with the truth extractor).

## Safety metrics (the point)

| Metric | Result |
|---|---|
| Wrongful wave-through rate (should-review cases routed clear-eligible) | 0% |
| Denials emitted (no-deny invariant; must be 0) | 0 |
| Conflict-detection recall | 100% |
| Recovery under injected failures (routed to human) | n/a (truth extractor only) |

## Quality metrics

| Metric | Result |
|---|---|
| Route accuracy vs labels | 100% |
| Screening decision accuracy | 100% |
| Extraction field accuracy (financial) | 100% |
| Mean latency per case | 44.1s |

## Notes

- **Extraction accuracy is 100%** because the synthetic documents are clean,
  single-page, text-based PDFs; Claude vision reads them without error. The
  confidence-bounding and conflict machinery exists for the harder real-world case
  (photographed, skewed, partial documents), which this synthetic set does not yet
  stress. That is the honest limitation: this measures that the pipeline is correct,
  not that vision is robust to degraded inputs.
- **Recovery is not measured under vision.** The failure injection corrupts a
  document's `truth` field, which only the deterministic extractor reads; the vision
  extractor reads the rendered PDF, so the injection cannot reach it. Recovery is
  100% with the truth extractor (`report.md`). Measuring it under vision would
  require re-rendering a corrupted PDF, noted as future work.
- **Latency (~44s/case)** is dominated by sequential vision calls over 3–4 documents
  per case. Batching or parallelizing extraction would cut this substantially.
