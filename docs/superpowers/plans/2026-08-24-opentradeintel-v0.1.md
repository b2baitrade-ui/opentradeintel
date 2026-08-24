# OpenTradeIntel v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, verify, publish, and release the OpenTradeIntel 0.1.0 deterministic procurement-matching toolkit.

**Architecture:** A modular Python package uses Pydantic contracts, local JSON/CSV parsers, pure normalization functions, a deterministic matcher, and one `OpportunityService`. Typer, FastAPI, and the dependency-free MCP adapter call the same service.

**Tech Stack:** Python >=3.12, uv, Pydantic 2, Typer, FastAPI, Uvicorn, pytest, Ruff, mypy, pre-commit, Docker, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-24-opentradeintel-v0.1-design.md`

## Global Constraints

- Package version is exactly `0.1.0` and `requires-python` is `>=3.12`.
- Core matching works without LLMs, API keys, network calls, or persistence.
- MCP is an adapter/interface without a runtime MCP dependency.
- CLI and FastAPI use the same `OpportunityService` and matching engine.
- Matching is deterministic, explainable, stable on ties, and scored from 0 to 100.
- All committed datasets are synthetic and explicitly labeled.
- No database, Redis, Celery, broker, frontend, embeddings, or vector store is introduced.
- The repository is not published before local quality gates and secret scan pass.
- Release `v0.1.0` is created only after the pushed GitHub CI is green.

## File map

- `src/opentradeintel/models/`: Pydantic domain and API output contracts.
- `src/opentradeintel/collectors/`: source acquisition protocol and local-file connector.
- `src/opentradeintel/parsers/`: JSON/CSV parsing protocols and implementations.
- `src/opentradeintel/normalization/`: pure text, category, unit, keyword, and market normalization.
- `src/opentradeintel/matching/`: deterministic scoring and result ranking.
- `src/opentradeintel/services.py`: the single orchestration layer shared by every interface.
- `src/opentradeintel/cli.py`: Typer presentation only.
- `src/opentradeintel/api/app.py`: FastAPI transport only.
- `src/opentradeintel/providers/` and `src/opentradeintel/mcp/`: dependency-free future extension contracts.
- `tests/unit/` and `tests/integration/`: behavior and transport verification.
- `docs/`, `examples/`, root OSS files, `.github/`: public documentation and operations.

---

### Task 1: Package foundation and domain models

**Files:**
- Create: `pyproject.toml`, `src/opentradeintel/__init__.py`, `src/opentradeintel/models/domain.py`, `src/opentradeintel/models/results.py`
- Test: `tests/unit/test_models.py`

**Interfaces:**
- Produces: `Tender`, `Product`, `ScoreBreakdown`, `MatchResult`, `MatchResponse`, and `__version__ = "0.1.0"`.

- [ ] Write model tests first for required fields, whitespace cleanup, currency normalization, non-negative quantities, date parsing, score bounds, and computed totals.
- [ ] Run `uv run pytest tests/unit/test_models.py -v` and confirm collection/import fails because the package is absent.
- [ ] Add the minimal package metadata and Pydantic models, using `Decimal | None` for quantities and `date | None` for deadlines.
- [ ] Run the model tests and retain a clean pass before continuing.

### Task 2: Ingestion contracts and JSON/CSV parsers

**Files:**
- Create: `src/opentradeintel/errors.py`, `src/opentradeintel/collectors/base.py`, `src/opentradeintel/collectors/files.py`, `src/opentradeintel/parsers/base.py`, `src/opentradeintel/parsers/json_parser.py`, `src/opentradeintel/parsers/csv_parser.py`, `src/opentradeintel/parsers/loader.py`
- Test: `tests/unit/test_parsers.py`

**Interfaces:**
- Consumes: `Tender.model_validate(data)` and `Product.model_validate(data)`.
- Produces: `LocalFileConnector.read_text(path: Path) -> str`, `load_tender(path: Path) -> Tender`, and `load_catalog(path: Path) -> list[Product]`.

- [ ] Add failing tests for a single JSON tender, wrapped/array JSON data, CSV product lists, JSON catalogs, uppercase suffixes, missing files, unsupported extensions, malformed JSON, and row-specific validation context.
- [ ] Run the parser test module and confirm failures identify missing ingestion code.
- [ ] Implement protocols, local reads, list coercion, JSON/CSV parsers, and suffix dispatch with typed domain exceptions.
- [ ] Run parser and model tests until both pass.

### Task 3: Normalization

**Files:**
- Create: `src/opentradeintel/normalization/text.py`, `src/opentradeintel/normalization/units.py`, `src/opentradeintel/normalization/categories.py`, `src/opentradeintel/normalization/keywords.py`, `src/opentradeintel/normalization/markets.py`, `src/opentradeintel/normalization/__init__.py`
- Test: `tests/unit/test_normalization.py`

**Interfaces:**
- Produces: `normalize_text(str) -> str`, `normalize_unit(str | None) -> str | None`, `normalize_category(str) -> str`, `extract_keywords(str, limit=20) -> list[str]`, and `market_tokens(str | Iterable[str]) -> set[str]`.

- [ ] Add failing tests for Unicode casefolding, punctuation/whitespace cleanup, unit aliases, category aliases, stable keyword extraction, stop-word removal, and EU market expansion.
- [ ] Run the focused tests and confirm expected missing-function failures.
- [ ] Implement pure deterministic functions and immutable alias maps.
- [ ] Run normalization tests and the accumulated suite.

### Task 4: Explainable deterministic matcher

**Files:**
- Create: `src/opentradeintel/matching/scorer.py`, `src/opentradeintel/matching/engine.py`, `src/opentradeintel/matching/__init__.py`
- Test: `tests/unit/test_scoring.py`, `tests/unit/test_matching.py`

**Interfaces:**
- Consumes: domain models and normalization functions.
- Produces: `score_product(tender: Tender, product: Product) -> MatchResult` and `DeterministicMatcher.match(tender: Tender, products: Sequence[Product], limit: int | None = None) -> list[MatchResult]`.

- [ ] Add failing scoring tests that independently prove the 40/15/20/15/10 components, neutral missing-MOQ score, score bounds, reasons, and warnings.
- [ ] Run scoring tests and confirm they fail because scorer behavior is missing.
- [ ] Implement the five component functions and sum their integer values into `ScoreBreakdown`.
- [ ] Run scoring tests to green.
- [ ] Add failing engine tests for descending rank, SKU tie-break, limits, empty catalogs, and input immutability.
- [ ] Implement stable ranking and validate a positive limit.
- [ ] Run all unit tests to green.

### Task 5: Shared service and CLI vertical slice

**Files:**
- Create: `src/opentradeintel/services.py`, `src/opentradeintel/cli.py`, `src/opentradeintel/__main__.py`, `examples/tenders/sample.json`, `examples/catalogs/sample.csv`, `examples/README.md`
- Test: `tests/unit/test_services.py`, `tests/integration/test_cli.py`

**Interfaces:**
- Produces: `OpportunityService.inspect_tender`, `OpportunityService.match`, `OpportunityService.match_files`, and console command `opentradeintel`.

- [ ] Add failing service tests proving parser/matcher orchestration and in-memory matching.
- [ ] Implement `OpportunityService` with constructor-injected matcher and no transport formatting.
- [ ] Add failing CLI tests for help, version, inspect, match, output explanations, and bad paths.
- [ ] Implement Typer commands as presentation wrappers over the service.
- [ ] Add clearly labeled synthetic examples and run the real sample match.
- [ ] Run accumulated tests plus `uv run opentradeintel --help` and the example command.

### Task 6: FastAPI, provider protocol, and MCP adapter

**Files:**
- Create: `src/opentradeintel/api/app.py`, `src/opentradeintel/api/schemas.py`, `src/opentradeintel/providers/base.py`, `src/opentradeintel/mcp/adapter.py`
- Test: `tests/integration/test_api.py`, `tests/unit/test_extension_interfaces.py`

**Interfaces:**
- Produces: `GET /health`, `GET /version`, `POST /match`, `EnrichmentProvider` protocol, and `OpenTradeIntelMCPAdapter.match_opportunity(tender, products, limit) -> MatchResponse`.

- [ ] Add failing API tests for health, version, matching, validation failure, and deterministic repeat responses.
- [ ] Implement a FastAPI app whose dependency returns the same service class used by CLI.
- [ ] Add failing structural tests proving the provider protocol and MCP adapter operate without provider/MCP packages.
- [ ] Implement the small protocols and delegate MCP matching to `OpportunityService`.
- [ ] Run the complete test suite.

### Task 7: Quality, documentation, community, and container files

**Files:**
- Create: `.editorconfig`, `.env.example`, `.gitignore`, `.pre-commit-config.yaml`, `LICENSE`, `README.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `ROADMAP.md`, `SECURITY.md`, `Makefile`, `Dockerfile`, `docker-compose.yml`, `docs/architecture.md`, `docs/connectors.md`, `docs/matching.md`, `docs/development.md`, `docs/oss-readiness.md`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `uv sync --all-groups`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src tests`, and `uv run pytest` quality commands.

- [ ] Configure Ruff, strict mypy, pytest, pre-commit, and uv dependency groups; generate `uv.lock` on Python 3.14.5.
- [ ] Write complete English documentation, Apache-2.0 licensing, privacy guidance, synthetic-data notice, contribution and security processes, and honest roadmap/readiness material.
- [ ] Create a non-root Python 3.12 Docker image and Compose healthcheck for `opentradeintel.api.app:app`.
- [ ] Run format, lint, type checking, tests, `docker compose config`, Docker build, and `/health` smoke test; fix only evidence-backed failures.

### Task 8: GitHub automation and templates

**Files:**
- Create: `.github/workflows/ci.yml`, `.github/workflows/security.yml`, `.github/dependabot.yml`, `.github/pull_request_template.md`, `.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/ISSUE_TEMPLATE/feature_request.yml`, `.github/ISSUE_TEMPLATE/config.yml`

**Interfaces:**
- CI tests Python `3.12`, `3.13`, and `3.14` with `contents: read`.
- CodeQL uses only `contents: read`, `security-events: write`, and `packages: read`.

- [ ] Add CI using checkout, setup-python, and setup-uv major-version actions, then execute the same locked Ruff, mypy, and pytest gates used locally.
- [ ] Add weekly CodeQL, monthly Dependabot for pip and Actions, valid issue forms, and a focused PR checklist.
- [ ] Validate all YAML through pre-commit and manually inspect workflow permissions and action sources.

### Task 9: Final local verification and secret scan

**Files:**
- Modify only files required by concrete verification failures.

**Interfaces:**
- Produces a clean repository eligible for publication.

- [ ] Run `uv sync --all-groups --locked`, Ruff check, Ruff format check, strict mypy, and full pytest with fresh output.
- [ ] Run CLI help/version/inspect/match smoke commands and API tests.
- [ ] Run `docker compose config`, build the image, start it, request `/health`, and stop it.
- [ ] Inspect `git diff --check`, `git status --short`, ignored `.env` behavior, tracked filenames, and likely secret patterns.
- [ ] Run a reputable local secret scanner without uploading repository contents and resolve any verified finding.

### Task 10: Commit, publish, CI, and release

**Files:**
- No source changes unless a local or remote check exposes a real defect; any defect receives a failing regression test first.

**Interfaces:**
- Produces public `https://github.com/b2baitrade-ui/opentradeintel` and release `v0.1.0` only after green CI.

- [ ] Stage all intended files, confirm no secrets/private data, and create one natural commit: `feat: initial OpenTradeIntel v0.1 foundation`.
- [ ] Re-run the complete quality gate after the commit.
- [ ] Create the public repository with the specified description, add `origin`, configure topics/issues, and push `main` without force.
- [ ] Poll the actual GitHub Actions runs until CI and security workflows complete; diagnose failures with logs and apply test-first fixes before repushing.
- [ ] After CI is green, create annotated tag and GitHub release `v0.1.0` with honest MVP notes.
- [ ] Verify repository visibility, default branch, rendered README metadata, detected license, topics, issues, Actions status, release, and remote URLs through GitHub APIs.
