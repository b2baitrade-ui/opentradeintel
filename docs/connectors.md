# Connectors and parsers

OpenTradeIntel separates **acquisition** from **interpretation**.

## Connector contract

`SourceConnector.read_text(path: Path) -> str` returns text and raises an OpenTradeIntel domain error when acquisition fails. Version 0.1 includes `LocalFileConnector`, which reads UTF-8 (including a UTF-8 BOM). Future HTTP, object-storage, or portal connectors should keep credentials outside source code and document rate limits and source terms.

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

HTML, RSS, PDF, XLSX, APIs, and public procurement portals are extension candidates, not partially implemented placeholders in v0.1.
