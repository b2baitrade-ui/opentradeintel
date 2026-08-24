# Deterministic matching

OpenTradeIntel's baseline matcher is local, repeatable, and explainable. It does not use random numbers, embeddings, language models, external taxonomies, or network calls.

## Formula

```text
Product similarity:       0..40
Category:                 0..15
Certifications:           0..20
Market compatibility:     0..15
MOQ compatibility:        0..10
--------------------------------
Total:                    0..100
```

### Product similarity

Tender tokens come from title, description, and requested products after Unicode, case, punctuation, and whitespace normalization. Product-name token coverage is worth 24 points. Product-keyword token coverage is worth 16. Each portion is proportional and rounded half up; an empty product keyword set contributes zero keyword points.

### Category

Known category aliases are canonicalized. The component receives 15 points when every product-category token appears in tender tokens; otherwise it receives zero and emits a warning.

### Certifications

Required and available certification names are normalized before exact comparison. Coverage is proportional to 20 points. A tender with no stated certification requirements receives all 20 points; missing requirements are listed in warnings.

### Market

A missing destination means there is no market restriction and receives 15 points. Otherwise, normalized destination and available-market tokens must intersect. Named EU member destinations expand to `eu`, allowing a catalog market such as `EU` or `Europe` to match Germany or France.

### MOQ

When both quantities exist, a tender quantity at or above the product MOQ receives 10 points; a shortfall receives zero and a warning. Missing tender quantity or product MOQ receives five neutral points and a verification warning.

## Ordering and interpretation

Results sort by descending total score. If both records provide CPV metadata, more exact CPV overlaps rank first among equal scores; the overlap is shown as a score-neutral explanation. Case-insensitive SKU remains the final deterministic tie-breaker. CPV prefixes and taxonomy relationships are not inferred.

A high score is evidence of structured-field compatibility—not a supplier qualification, legal conclusion, price comparison, sanctions check, product-quality decision, or award recommendation. Operators should review warnings and verify commercial units, certifications, market rights, and current supplier capacity.

## Evolving the matcher

Changes to weights or normalization are public behavior changes. They require hand-derived regression cases and a changelog entry. Optional semantic methods should report their own evidence and remain distinguishable from the deterministic baseline.
