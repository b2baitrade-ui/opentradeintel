# Architecture

OpenTradeIntel 0.1 is a modular monolith. It favors explicit contracts and pure functions over infrastructure that the baseline does not need.

## Data flow

```text
Local JSON/CSV
  -> SourceConnector
  -> TenderParser / CatalogParser
  -> Tender / Product
  -> normalization
  -> DeterministicMatcher
  -> OpportunityService
     -> Typer CLI
     -> FastAPI
     -> MCP adapter
```

## Boundaries

- `models` owns validation and serialization contracts.
- `collectors` acquires raw text without interpreting it.
- `parsers` turns source text into typed models.
- `normalization` contains deterministic, side-effect-free helpers.
- `matching` owns component scoring and stable ranking.
- `services.py` orchestrates loading and matching.
- `cli` and `api` only translate input/output for their transports.
- `providers` and `mcp` define optional integration boundaries.

The API and CLI do not import scoring internals. This keeps one behavior path and makes later interfaces consumers of the same service rather than alternate implementations.

## Design principles

- **Open by default:** Apache-2.0 source, public contracts, and ordinary file formats.
- **Self-hostable:** no managed service is required.
- **AI optional:** deterministic core behavior has no provider dependency.
- **Explainable scoring:** every point belongs to a visible component.
- **Provider agnostic:** future enrichment implements a protocol, not a vendor-specific core.
- **Extensible connectors:** acquisition and parsing are separate interfaces.
- **Structured data first:** matching starts only after model validation.
- **Privacy-conscious:** source data stays local unless an operator explicitly adds an integration.
- **Testable:** pure helpers and one service boundary minimize hidden state.

## Deliberate omissions

Version 0.1 has no repository/database layer because it does not persist state. It also has no queue, scheduler, cache, vector database, frontend, embeddings, portal scraper, or live MCP server. These would increase operational and security cost without improving the local baseline.

## Extension direction

A new connector should implement `SourceConnector`; a new parser should implement `TenderParser` or `CatalogParser`. Future semantic rankers can complement, but should not silently replace, the deterministic baseline. A concrete MCP package can register `OpenTradeIntelMCPAdapter.match_opportunity` with a supported runtime without moving SDK imports into core.
