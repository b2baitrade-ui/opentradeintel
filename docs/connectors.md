# Connectors and parsers

OpenTradeIntel separates **acquisition** from **interpretation**.

## Connector contract

`SourceConnector.read_text(path: Path) -> str` returns text and raises an OpenTradeIntel domain error when acquisition fails. `LocalFileConnector` reads UTF-8 (including a UTF-8 BOM).

Search APIs use a capability-specific client when a path-to-text contract would hide important semantics. The official TED integration is split into:

- `TEDSearchQuery`: validates filters and renders an expert query;
- `TEDSearchClient`: owns HTTP, response-envelope validation, and pagination;
- `TEDNoticeMapper`: maps raw field projections to `Tender` without network access;
- `TEDOpportunityService`: composes search/mapping with the existing matcher.

This split is the connector contract: acquisition returns validated raw source data, mapping creates generic typed models, and an application service composes existing business logic. See [official TED source notes](sources/ted.md).

`TEDSearchClient` streams each response and enforces a 16 MiB decoded-body ceiling by default. It rejects an oversized declared `Content-Length` before reading and also stops if streamed bytes cross the ceiling. Integrators can set a smaller positive `max_response_bytes` value when constructing the client.

## Parser contracts

- `TenderParser.parse(text, source) -> Tender`
- `CatalogParser.parse(text, source) -> list[Product]`

Parsers must validate through the domain models and include source/record context in failures. They must not fetch URLs, call AI providers, or hide invalid rows.

## Supported formats

### JSON

A tender may be one object, a one-item array, or `{ "tenders": [...] }`. A catalog may be one product object, an array, or `{ "products": [...] }`.

### CSV

CSV uses one record per row. List-valued columns use semicolons:

```csv
certifications,available_markets,keywords
"EU Organic;HACCP","EU;Singapore","mango;organic"
```

Both tenders and catalogs are accepted as JSON or CSV. Tender CSV files must contain exactly one data row.

## Adding a format

1. Start with failing parser tests for valid, invalid, empty, and multi-record input.
2. Implement the appropriate parser protocol in a focused module.
3. Preserve domain validation instead of duplicating field rules.
4. Register the suffix in `parsers/loader.py` only after the tests pass.
5. Document encoding, list conventions, and lossy transformations.

## Public API checklist

1. Use an official documented API when available.
2. Configure base URL, timeout, and an identifying user-agent.
3. Validate request inputs and response envelopes explicitly.
4. Keep retries absent or small, visible, bounded, and justified.
5. Exercise success, empty, malformed, timeout, network, pagination, and mapping behavior offline.
6. Preserve source identifiers and URLs with optional generic model fields.
7. Attribute any redistributable public fixture and keep supplier examples synthetic.

HTML scraping, RSS, PDF, and XLSX remain unsupported unless a complete, tested connector/parser is contributed.
