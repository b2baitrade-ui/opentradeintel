# Architecture

OpenTradeIntel is a modular monolith. It favors explicit contracts and pure functions over infrastructure that the current product does not need.

## Data flow

```text
Local JSON/CSV -> SourceConnector -> TenderParser / CatalogParser -> Tender / Product --\
                                                                                        -> OpportunityService -> matcher
Official TED -> TEDSearchClient -> TEDNoticeMapper -> TEDOpportunityService -----------/                         -> Typer CLI

Typed Tender / Product ---------------------------------------------------------------> OpportunityService -> FastAPI / MCP adapter
```

## Boundaries

- `models` owns validation and serialization contracts.
- `collectors` owns source acquisition clients and keeps source mapping pure and separate from transport I/O.
- `parsers` turns source text into typed models.
- `normalization` contains deterministic, side-effect-free helpers.
- `matching` owns component scoring and stable ranking.
- `services.py` orchestrates loading and matching.
- `ted_service.py` composes official TED search/mapping with `OpportunityService`.
- `cli` and `api` only translate input/output for their transports. In v0.2, TED search is exposed by the CLI; FastAPI and the MCP adapter accept already typed records for matching.
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

The project has no repository/database layer because it does not persist state. It also has no queue, scheduler, cache, vector database, frontend, embeddings, portal scraper, or live MCP server. These would increase operational and security cost without improving the current workflows.

## Extension direction

A new file connector should implement `SourceConnector`; a new API connector should keep client, response validation, mapping, and application composition separate. A new parser should implement `TenderParser` or `CatalogParser`. Future semantic rankers can complement, but should not silently replace, the deterministic baseline. A concrete MCP package can register `OpenTradeIntelMCPAdapter.match_opportunity` with a supported runtime without moving SDK imports into core.
