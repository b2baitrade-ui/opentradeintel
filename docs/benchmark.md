# Matcher benchmark

OpenTradeIntel tracks deterministic ranking quality with a committed synthetic benchmark. The baseline is not a claim about production procurement accuracy; it is a reproducible regression signal for changes to matching, normalization, and future scoring weights.

## Dataset

`benchmarks/dataset.json` contains:

- 20 synthetic procurement opportunities;
- 30 synthetic supplier products;
- hand-authored binary relevance labels;
- positive, negative, ambiguous, certification, market, MOQ, and category cases;
- no live data, confidential data, AI-generated labels, or network dependency.

Run it from the repository root:

```bash
uv run python benchmarks/run.py
```

## Baseline

Measured on 2026-08-24 with the v0.2 candidate matcher:

```text
OpenTradeIntel synthetic matcher benchmark
Products: 30
Opportunities: 20
precision@1: 0.9500
precision@3: 0.3667
MRR: 0.9750
False-positive examples:
  BENCH-020: predicted FURN-CHAIR (score 76); relevant FURN-DESK
False-negative examples:
  BENCH-005: FOOD-RAISINS ranked 4
```

`precision@k` is the mean fraction of the first `k` results included in each opportunity's relevance labels. Because most cases intentionally have one relevant SKU, precision@3 is not expected to approach 1.0. MRR is the mean reciprocal rank of the first relevant result.

## Known failure modes

- Broad category wording can leave similar products tied, making the SKU fallback decide between them, as in `BENCH-020`.
- A broad requirement with more than three acceptable variants necessarily leaves some relevant products outside the first three, as in `BENCH-005`.
- Exact token coverage does not infer synonyms outside the explicit normalization tables.
- Exact CPV overlap is currently a score-neutral tie-break signal; CPV hierarchy is not inferred.
- Missing quantity or MOQ receives neutral points and requires operator review.

Any score-weight change must update focused regression tests, rerun this benchmark, explain the delta, and keep the previous result discoverable in version history.
