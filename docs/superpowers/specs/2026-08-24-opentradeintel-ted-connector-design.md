# OpenTradeIntel TED Connector Design

**Date:** 2026-08-24
**Status:** Approved for implementation
**Target release:** v0.2.0, subject to green quality gates and release readiness

## Goal

Add one production-quality public procurement connector for the official TED Search API while preserving the v0.1 architecture and its deterministic, local-first matching core.

The supported flow is:

```text
official TED Search API
  -> validated raw response
  -> deterministic TED notice mapper
  -> generic Tender models
  -> existing OpportunityService
  -> existing deterministic matcher
  -> CLI output
```

No database, queue, scheduler, scraper, browser automation, LLM, embedding model, or API key is introduced.

## Official contract

The connector uses only `POST https://api.ted.europa.eu/v3/notices/search`. Published-notice search is public and does not require authentication.

The request uses an expert query plus an explicit field projection. The connector supports:

- keyword phrases through the official `FT ~ "..."` field expression;
- CPV through `classification-cpv = ...`;
- place of performance through `place-of-performance = ...`;
- `ACTIVE`, `LATEST`, and `ALL` scopes;
- `PAGE_NUMBER` and `ITERATION` pagination modes;
- the documented maximum of 250 notices per request.

The client reads `notices`, `totalNoticeCount`, `iterationNextToken`, and `timedOut`. It stops at the caller's bounded result limit and never retries implicitly.

Official references and field-level notes are maintained in `docs/sources/ted.md`.

## Components

### `TEDSearchQuery`

A validated, immutable query value object. It accepts an optional keyword, CPV expression, and country/place code, requires at least one filter, and renders a deterministic expert query. User text is quoted and escaped. CPV and country inputs are constrained before a network request is made.

The CLI accepts common two-letter EU country codes and maps them to the three-letter TED values documented by TED expert-search examples. Three-letter TED values remain accepted directly.

### `TEDSearchClient`

A synchronous public API client with:

- configurable base URL, timeout, and user-agent;
- an injectable `httpx2.Client`, allowing real request behavior to be tested with `MockTransport`;
- explicit timeout, network, HTTP status, JSON, schema, and TED timeout errors;
- page-number and iteration-token pagination;
- no hidden retries;
- response validation before notices reach the mapper.

The client owns and closes only HTTP clients it creates itself.

### `TEDNoticeMapper`

A pure deterministic mapper. It has no network access and maps one validated raw notice to the generic `Tender` model.

Multilingual fields prefer English, then choose the lexicographically first available language. List values are deduplicated without reordering. Missing required v0.1 text fields receive explicit neutral fallbacks such as `TED notice <publication-number>` and `Buyer not specified`, rather than inventing procurement facts.

The mapper preserves:

- TED publication number as `id` and `source_id`;
- TED detail URL as `source_url`;
- title, buyer, and procedure/lot descriptions;
- CPV codes and NUTS/place-of-performance codes;
- earliest tender deadline when supplied;
- procedure estimated value and currency when supplied;
- publication date;
- `source="TED"`.

Quantity, unit, and certifications remain unset unless the selected API fields provide unambiguous procedure-level semantics.

### `TEDOpportunityService`

A small application service composes the client, mapper, existing catalog loader, and existing `OpportunityService`. It exposes search and search-and-match use cases. CLI code does not construct expert queries, inspect TED response fields, or call the matcher directly.

Future HTTP or MCP adapters can call the same service without duplicating TED business logic. No TED FastAPI endpoint is required for v0.2.

## Backward-compatible domain changes

`Tender` gains optional, source-neutral metadata:

- `source_id`
- `source_url`
- `cpv_codes`
- `nuts_codes`
- `estimated_value`
- `publication_date`

`Product` gains optional `cpv_codes`. Existing JSON and CSV inputs remain valid because all new fields have defaults. CSV list parsing is extended for the new code lists.

## CPV matching behavior

The existing five score components and their exact 0–100 total remain unchanged. When a tender and a product share an exact normalized CPV code:

- the match explanation records the overlap;
- equal-score results with more exact CPV overlap rank first;
- SKU remains the final stable tie-breaker.

This adds a deterministic signal without silently redefining the published score. Hierarchical CPV similarity and score weights are deferred until benchmark evidence supports them.

## CLI

Two commands are added under a `ted` command group:

```text
opentradeintel ted search --query "dried fruit" --limit 10 --output json
opentradeintel ted search --cpv 15897200 --country DE --output-file tenders.json
opentradeintel ted match --query "dried fruit" --catalog catalog.csv
```

`search` prints a concise text view by default or normalized JSON with `--output json`. `--output-file` always writes normalized JSON atomically enough for a local CLI use case: the destination is validated and overwritten only after successful search and serialization.

`match` uses the same query options and service composition, then renders ranked catalog matches for each returned tender. JSON output is also available for automation.

## Error handling

Expected failures are subclasses of `OpenTradeIntelError` and produce stable CLI messages without tracebacks. They distinguish:

- timeout;
- network failure;
- non-success HTTP response;
- invalid JSON or malformed response schema;
- server-side search timeout;
- unmappable notice data;
- invalid user query.

Errors contain safe diagnostics but never response bodies large enough to leak or flood terminal output.

## Testing

All default tests are offline. A trimmed public TED response fixture mirrors the real API shape and includes source attribution. Test coverage includes request construction, pagination, iteration tokens, empty/malformed responses, timeout/network/status failures, multilingual and optional-field mapping, CPV/NUTS/deadlines, CLI JSON/file output, and fixture-to-match composition.

An optional `live` pytest marker performs a single bounded public query and is excluded from default CI with `-m "not live"`.

## Benchmark

`benchmarks/` contains a reproducible synthetic dataset with at least 20 opportunities, 30 products, and hand-authored binary relevance labels. `uv run python benchmarks/run.py` reports precision@1, precision@3, MRR, and concrete false-positive/false-negative examples. No labels are generated by AI or live services.

The first baseline is recorded before any future score-weight change. The CPV tie-break behavior does not alter component weights.

## Distribution and supply chain

The project version becomes `0.2.0` only when the feature, documentation, benchmark, and quality gates are complete. A release workflow builds distributions, validates them, transfers them as artifacts, and publishes through PyPI Trusted Publishing with job-scoped `id-token: write` and the `pypi` GitHub environment. No long-lived PyPI token is used.

GitHub Actions in security-sensitive workflows are pinned to immutable commit SHAs with readable version comments. Dependabot continues to update GitHub Actions.

The PyPI project name currently has no JSON project endpoint, but actual first-project reservation requires a user to configure a pending Trusted Publisher in the PyPI UI. Release publication stops until that user action is confirmed.

## Branch protection

The repository currently has no main protection or ruleset. A repository-scoped ruleset or branch protection configuration will be attempted only if it can require PRs, CI, and CodeQL while retaining an administrator bypass for the sole maintainer. Force pushes and branch deletion must remain blocked. If the repository plan/API cannot express this safely, the limitation is documented and no workaround is used.

## Non-goals

- Full TED field coverage or XML parsing
- Bid/no-bid automation
- CPV taxonomy download or fuzzy hierarchy scoring
- Scheduled ingestion or persistence
- FastAPI TED routes
- Runtime MCP integration
- Automated PyPI account or environment UI changes
