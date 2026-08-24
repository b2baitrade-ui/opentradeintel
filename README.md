# OpenTradeIntel

> Open-source procurement and B2B sourcing intelligence engine.

[![CI](https://github.com/b2baitrade-ui/opentradeintel/actions/workflows/ci.yml/badge.svg)](https://github.com/b2baitrade-ui/opentradeintel/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-%3E%3D3.12-3776AB)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

OpenTradeIntel turns fragmented tender/RFQ datasets and supplier catalogs into structured, ranked business opportunities. It is an early-stage, self-hosted toolkit for SMEs, exporters, sourcing and procurement teams, researchers, developers, and trade-intelligence projects.

## Why?

Procurement requirements and catalogs often arrive in incompatible spreadsheets or data exports. OpenTradeIntel provides a small, inspectable baseline for validating that data, normalizing common terms, and explaining why one catalog product ranks above another—without sending commercial data to an external AI service.

## Features

- Typed tender/RFQ and product models using Pydantic.
- JSON and CSV ingestion behind extensible connector/parser interfaces.
- Local text, unit, category, keyword, and market normalization.
- Deterministic 0–100 matching with a complete component breakdown.
- Typer CLI and FastAPI API backed by the same application service.
- Dependency-free MCP adapter and optional provider protocol.
- Synthetic examples, tests, Docker packaging, and OSS project files.
- No API key, LLM, database, queue, or network call required by core features.

## Quick start

Requirements: Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/b2baitrade-ui/opentradeintel.git
cd opentradeintel
uv sync --all-groups --locked
uv run opentradeintel --help
```

Inspect the synthetic tender:

```bash
uv run opentradeintel inspect examples/tenders/sample.json
```

Match it against the synthetic catalog:

```bash
uv run opentradeintel match \
  --tender examples/tenders/sample.json \
  --catalog examples/catalogs/sample.csv
```

Example excerpt (values are computed, not hard-coded):

```text
1. Dried Mango 500g
   Score: 100/100

   Reasons:
   [+] Product similarity: 40/40 (name 24/24, keywords 16/16)
   [+] Category: 15/15 (dried fruit)
   [+] Certifications: 20/20 (2/2 covered)
   [+] Market compatibility: 15/15
   [+] MOQ compatibility: 10/10
```

All included examples are synthetic and provided for demonstration purposes only.

## API

Start the API:

```bash
uv run uvicorn opentradeintel.api.app:app --reload
```

Available routes:

- `GET /health`
- `GET /version`
- `POST /match`
- Interactive OpenAPI documentation at `/docs`

Minimal request:

```bash
curl -X POST http://127.0.0.1:8000/match \
  -H "Content-Type: application/json" \
  -d '{
    "tender": {
      "id": "demo-rfq", "title": "Dried mango", "buyer": "Demo Buyer",
      "description": "Organic dried fruit", "products": ["mango"],
      "quantity": 1000, "unit": "kg", "destination": "Germany",
      "currency": "EUR", "required_certifications": ["EU Organic"],
      "source": "synthetic-demo"
    },
    "products": [{
      "sku": "DM-1", "name": "Dried mango", "description": "Organic slices",
      "category": "Dried fruit", "origin": "Exampleland",
      "certifications": ["EU Organic"], "min_order_quantity": 100,
      "available_markets": ["EU"], "keywords": ["mango", "organic"]
    }]
  }'
```

## How matching works

The score is the integer sum of five deterministic components:

| Component | Maximum | Baseline behavior |
| --- | ---: | --- |
| Product similarity | 40 | Product-name token coverage (24) plus keyword coverage (16) |
| Category | 15 | Normalized category tokens appear in the tender |
| Certifications | 20 | Proportional coverage of required certifications |
| Market | 15 | Destination and available-market aliases intersect |
| MOQ | 10 | Tender quantity meets product minimum order quantity |

Missing quantity or MOQ receives five neutral points and a warning. Results include reasons, warnings, and the component breakdown. Ties are sorted by SKU, so identical inputs always produce identical output. See [matching documentation](docs/matching.md).

## Architecture

```text
source -> connector -> JSON/CSV parser -> typed models -> normalization
       -> deterministic matcher -> OpportunityService -> CLI / FastAPI / MCP adapter
```

The boundaries are intentionally small. New source connectors acquire text; parsers interpret formats; interfaces never reimplement matching. See [architecture](docs/architecture.md) and [connector guidance](docs/connectors.md).

## Data privacy

OpenTradeIntel does not require procurement or supplier data to be sent to an external AI API. The default workflow is local, deterministic, and suitable for self-hosting. Users remain responsible for access control, retention, applicable procurement rules, and the accuracy of final commercial decisions.

## AI providers and MCP

AI is optional. The `EnrichmentProvider` protocol is a future extension point; no provider is installed or called by core. `.env.example` contains a blank optional key only to document that future integration. Version 0.1 also ships a dependency-free `OpenTradeIntelMCPAdapter`; registering it with a concrete MCP SDK is deferred to v0.2.

## Docker

```bash
docker compose up --build
curl http://127.0.0.1:8000/health
```

The runtime image uses Python 3.12, runs as a non-root user, and exposes port `8000`.

## Developing

```bash
uv sync --all-groups --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
```

On systems with GNU Make, `make check` runs the same gates. See [development documentation](docs/development.md).

## Roadmap

Version 0.1 focuses on a dependable local baseline. PDF/XLSX parsing, plugin connectors, semantic matching, and a concrete MCP server are candidates for v0.2. See the honest, non-binding [roadmap](ROADMAP.md).

## Contributing

Issues and pull requests are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before adding a parser or connector, and follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Do not open a public issue for a vulnerability. Follow the private reporting instructions in [SECURITY.md](SECURITY.md).

## License

Licensed under the [Apache License 2.0](LICENSE).
