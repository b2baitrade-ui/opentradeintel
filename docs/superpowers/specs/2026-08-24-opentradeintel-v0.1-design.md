# OpenTradeIntel v0.1 Design

## Purpose

OpenTradeIntel is a self-hosted Python toolkit that turns synthetic or user-supplied tender/RFQ records and supplier catalogs into structured, ranked, and explainable product opportunities. Its baseline workflow is local and deterministic; it neither requires nor contacts an AI provider.

## Scope

Version 0.1 includes typed tender and product models, local JSON/CSV ingestion, text and unit normalization, deterministic matching, one application service, a Typer CLI, a FastAPI API, synthetic examples, Docker packaging, tests, documentation, and minimal GitHub automation. It deliberately excludes persistence, queues, brokers, databases, embeddings, LLM calls, portal-specific connectors, and a runtime MCP dependency.

## Design principles

- Open by default and licensed under Apache-2.0.
- Self-hostable, privacy-conscious, and usable offline after installation.
- AI optional and provider agnostic.
- Structured data first, with deterministic and explainable scoring.
- Small interfaces for connectors, parsers, providers, and MCP adapters.
- One business-logic path shared by CLI and API.
- Testable units with explicit validation and predictable errors.

## Architecture

The package is a modular monolith under `src/opentradeintel`. Pydantic models define input and output contracts. Local file connectors provide text to format-specific parsers. Normalization functions are pure. `DeterministicMatcher` calculates score components and explanations. `OpportunityService` owns file loading and matching orchestration; both Typer and FastAPI call this service.

```text
JSON/CSV files
    -> LocalFileConnector
    -> JSON or CSV parser
    -> Pydantic Tender/Product models
    -> normalization functions
    -> DeterministicMatcher
    -> OpportunityService
       -> Typer CLI
       -> FastAPI
```

`providers` exposes an optional enrichment protocol but no provider implementation. `mcp` exposes an adapter with a `match_opportunity` method but imports no MCP SDK.

## Models

`Tender` contains `id`, `title`, `buyer`, `description`, `products`, `quantity`, `unit`, `destination`, `deadline`, `currency`, `required_certifications`, and `source`. `Product` contains `sku`, `name`, `description`, `category`, `origin`, `certifications`, `min_order_quantity`, `available_markets`, and `keywords`. Quantities use `Decimal`; deadlines use `date`; currency codes are uppercased and validated as three letters.

`MatchResult` contains a 0–100 integer score, the matched product, reasons, warnings, and a component breakdown.

## Ingestion

`SourceConnector` is a protocol whose `read_text(Path) -> str` contract separates acquisition from parsing. Version 0.1 supplies `LocalFileConnector`. `TenderParser` and `CatalogParser` protocols make parser implementations replaceable. JSON accepts one tender object, one product object, an array, or an object with `tenders`/`products`; CSV accepts one record per row. List-valued CSV columns use semicolon-separated values.

The application loader selects a parser by the lowercase file suffix and raises a clear `UnsupportedFormatError` for unknown formats. Validation errors retain the source filename and record index.

## Normalization

Pure functions perform Unicode normalization, lowercase conversion, whitespace cleanup, punctuation-to-space conversion, unit aliases (`kilogram`, `kilograms`, `kgs` to `kg`), basic category aliases, stop-word-filtered keyword extraction, and market aliases. Germany and other named EU markets expand to include `eu`; matching does not rely on remote taxonomies.

## Deterministic scoring

Every product is scored using exactly five components:

- Product similarity — 40 points: 24 points for normalized product-name token coverage in tender text and 16 points for product-keyword coverage. Empty keyword sets contribute zero keyword points.
- Category — 15 points: full points when the normalized product category appears in normalized tender categories/text, otherwise zero.
- Certifications — 20 points: proportional coverage of required certifications; full points when the tender states no certification requirement.
- Market compatibility — 15 points: full points when destination aliases intersect available-market aliases; full points when no destination restriction exists; otherwise zero.
- MOQ compatibility — 10 points: full points when tender quantity is at least product MOQ, zero when below MOQ, and five neutral points with a warning when either value is unavailable.

Each fractional component is rounded only after multiplication. The integer component scores sum to the final score and never contain randomness. Reasons describe awarded points; warnings describe missing metadata, unmet certifications, unsupported markets, or MOQ shortfalls. Results sort by descending score and then by casefolded SKU for stable ties.

## Interfaces and errors

`OpportunityService.inspect_tender(path)` returns a validated `Tender`. `OpportunityService.match_files(tender_path, catalog_path, limit)` returns a `MatchResponse`. `OpportunityService.match(tender, products, limit)` is the in-memory entry point used by the API and MCP adapter.

The CLI converts domain and validation exceptions to readable stderr messages and a non-zero exit. FastAPI converts invalid request bodies to its standard 422 response and domain errors to 400. Unexpected exceptions remain visible during development and are not masked with misleading success responses.

## Testing

Development follows red-green-refactor. Unit tests cover model validation, parsers, loaders, normalization, every score component, ordering, warnings, and service behavior. Integration tests cover CLI help/version/inspect/match and API health/version/match. At least 30 behavior-focused tests are expected. Quality gates are Ruff formatting/lint, strict mypy, and pytest on Python 3.12–3.14.

## Operations and publication

`uv` manages environments and the lockfile. A Makefile documents Linux/CI shortcuts, while Windows verification uses equivalent `uv run` commands. Docker runs Uvicorn as a non-root user. GitHub Actions use `contents: read` in CI and narrowly scoped CodeQL permissions. Publication happens only after local checks and a local secret scan. Tag and release `v0.1.0` happen only after the pushed CI run succeeds.

## Synthetic data and privacy

All committed examples use invented organizations, identifiers, products, and commercial details and are labeled synthetic. No credentials or customer data are stored. `.env` is ignored; `.env.example` contains only blank optional variables. External AI use remains an opt-in future extension.
