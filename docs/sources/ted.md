# TED official source notes

OpenTradeIntel uses only the official Tenders Electronic Daily (TED) Search API operated by the Publications Office of the European Union.

## API contract used

- API generation: TED API v3
- Production endpoint: `POST https://api.ted.europa.eu/v3/notices/search`
- Authentication: none for published-notice search
- Request content type: `application/json`
- Search syntax: TED Expert Search expressions
- Pagination: `PAGE_NUMBER` or `ITERATION`
- Maximum notices per request: 250
- Page-number retrieval ceiling: 15,000 matching notices
- Iteration retrieval ceiling: no total-result ceiling documented; each page remains bounded to 250
- Field-volume ceiling: 10,000 returned fields per page

The connector makes bounded calls and never retries implicitly. `PAGE_NUMBER` increments the one-based `page`; `ITERATION` sends the opaque `iterationNextToken` returned by the preceding response.

## Request and response fields

The v0.2 connector requests this explicit projection:

| TED field | OpenTradeIntel use |
| --- | --- |
| `publication-number` | `Tender.id`, `Tender.source_id` |
| `notice-title` | title, English preferred |
| `buyer-name` | buyer, English preferred |
| `description-proc`, `description-lot` | description |
| `classification-cpv`, `main-classification-proc` | deduplicated CPV codes |
| `place-of-performance` | NUTS/place codes and destination |
| `deadline-receipt-tender-date-lot`, `deadline-date-lot` | earliest supplied tender deadline |
| `publication-date` | publication date |
| `estimated-value-proc`, `estimated-value-cur-proc` | estimated procedure value and currency |
| `links` | English TED detail URL where present |

The response envelope is validated for `notices`, `totalNoticeCount`, optional `iterationNextToken`, and `timedOut`. The field projection remains variable by TED's design, so the mapper validates relevant values and tolerates missing optional fields.

A production probe on 2026-08-24 confirmed that `estimated-value-proc` can be encoded as a JSON string even though the OpenAPI schema describes a number. The mapper therefore accepts either a decimal-compatible string or number and emits a typed `Decimal`.

## Query mapping

- `--query "dried fruit"` becomes `FT ~ "dried fruit"`.
- `--cpv 15897200` becomes `classification-cpv = 15897200`.
- `--cpv 15*` preserves TED's documented prefix wildcard.
- `--country DE` is normalized to the TED country value `DEU` and becomes `place-of-performance = DEU`.
- Multiple filters are combined with `AND` in a fixed order.

CPV and place of performance are hierarchical TED fields. OpenTradeIntel stores returned codes but does not bundle a taxonomy or infer hierarchy in v0.2.

## Official references

- [TED Search API overview](https://docs.ted.europa.eu/api/latest/search.html)
- [Official v3 Swagger UI](https://api.ted.europa.eu/swagger-ui/index.html)
- [Official v3 OpenAPI document](https://api.ted.europa.eu/api-v3.yaml)
- [Search API modes and limits](https://docs.ted.europa.eu/ODS/latest/reuse/search-api.html)
- [TED Expert Search syntax and examples](https://ted.europa.eu/en/help/search-browse)
- [TED search field list](https://docs.ted.europa.eu/ODS/latest/reuse/field-list.html)
- [Official notice direct-link formats](https://docs.ted.europa.eu/ODS/latest/reuse/download-direct.html)

## Fixture attribution

`tests/fixtures/ted/search_success.json` and `examples/ted/notice-search-response.json` are trimmed public-data snapshots derived from official notice [176184-2026](https://ted.europa.eu/en/notice/-/detail/176184-2026), retrieved through the official Search API on 2026-08-24. Unused translations and download variants were removed to keep tests focused. The data is public procurement information, not a synthetic supplier record and not confidential data.
