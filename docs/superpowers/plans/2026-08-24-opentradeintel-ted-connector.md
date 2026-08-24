# OpenTradeIntel TED Connector Implementation Plan

> **For maintainers:** Execute each task test-first. Every behavior test must be observed failing before production code is added.

**Goal:** Ship a backward-compatible v0.2.0 candidate that queries the official TED Search API, maps notices into `Tender`, matches them against a local catalog, and establishes an offline quality benchmark and secure PyPI release path.

**Architecture:** A transport-focused `TEDSearchClient` and pure `TEDNoticeMapper` feed a `TEDOpportunityService` that composes the existing `OpportunityService`. The CLI is an adapter only. CPV overlap is a score-neutral deterministic tie-break signal.

**Tech stack:** Python 3.12+, Pydantic 2, httpx2, Typer, pytest, uv, Ruff, mypy, GitHub Actions.

---

## Task 1: Official-source record and fixture

**Files:**
- Create: `docs/sources/ted.md`
- Create: `tests/fixtures/ted/search_success.json`
- Create: `tests/fixtures/ted/search_empty.json`
- Create: `tests/fixtures/ted/search_malformed.json`
- Create: `examples/ted/README.md`
- Create: `examples/ted/notice-search-response.json`

1. Document the official v3 endpoint, no-auth access, request/response fields, modes, limits, selected fields, and retrieval attribution with direct official URLs.
2. Add a trimmed, attributed public response shaped like the verified API response and separate empty/malformed fixtures.
3. Verify every committed fixture contains no credentials and clearly distinguishes public data from synthetic examples.

## Task 2: Backward-compatible domain metadata

**Files:**
- Modify: `src/opentradeintel/models/domain.py`
- Modify: `src/opentradeintel/parsers/csv_parser.py`
- Modify: `tests/unit/test_models.py`
- Modify: `tests/unit/test_parsers.py`

1. Write failing tests for optional tender source metadata, CPV/NUTS normalization, estimated value/publication date, product CPV, and CSV code-list parsing.
2. Run the focused tests and confirm RED because the fields are rejected or unparsed.
3. Add the optional generic fields and stable code normalization with no changes to existing required inputs.
4. Extend CSV list-field handling.
5. Run focused tests and confirm GREEN; run existing model/parser tests for regression.

## Task 3: TED query and HTTP client

**Files:**
- Create: `src/opentradeintel/collectors/ted.py`
- Modify: `src/opentradeintel/collectors/__init__.py`
- Modify: `src/opentradeintel/errors.py`
- Create: `tests/unit/test_ted_client.py`
- Modify: `pyproject.toml`
- Modify: `uv.lock`

1. Write failing tests for literal request construction, two-letter EU country mapping, invalid CPV/country/query, configured URL/timeout/user-agent, successful/empty responses, HTTP error, malformed JSON/schema, timeout, network error, server timeout, multi-page page-number traversal, iteration-token traversal, and result-limit bounding.
2. Run the new test module and confirm RED because TED types do not exist.
3. Move `httpx2` into runtime dependencies and refresh the lockfile.
4. Implement `TEDSearchQuery`, validated response models, and `TEDSearchClient` with injected real HTTP client behavior and no retries.
5. Run the focused tests and confirm GREEN.

## Task 4: TED notice mapping

**Files:**
- Modify: `src/opentradeintel/collectors/ted.py`
- Create: `tests/unit/test_ted_mapper.py`

1. Write failing fixture-backed tests for publication number, multilingual title/buyer/description, URL preference, CPV, NUTS, deadline, estimated value/currency, publication date, deduplication, and missing optional fields.
2. Add tests for missing publication number and structurally invalid relevant fields.
3. Run tests and confirm RED because the mapper does not exist.
4. Implement the pure `TEDNoticeMapper` with deterministic language and fallback rules.
5. Run focused tests and confirm GREEN.

## Task 5: CPV score-neutral signal

**Files:**
- Modify: `src/opentradeintel/matching/scorer.py`
- Modify: `src/opentradeintel/matching/engine.py`
- Modify: `tests/unit/test_scoring.py`
- Modify: `tests/unit/test_matching.py`
- Modify: `docs/matching.md`

1. Write failing tests proving exact CPV overlap adds an explanation, does not change the score/breakdown, wins an otherwise equal-score tie, and still falls back to casefolded SKU.
2. Run focused tests and confirm RED.
3. Implement exact normalized overlap and deterministic sorting.
4. Run focused and existing matcher tests and confirm GREEN.
5. Document that CPV is a tie-break signal, not a sixth score component.

## Task 6: Shared TED application service

**Files:**
- Create: `src/opentradeintel/ted_service.py`
- Create: `tests/unit/test_ted_service.py`

1. Write failing tests for raw-search mapping, ordered output, empty search, catalog loading, per-tender match composition, and propagated connector errors.
2. Run tests and confirm RED.
3. Implement `TEDOpportunityService` using `TEDSearchClient`, `TEDNoticeMapper`, catalog loading, and the existing `OpportunityService`.
4. Run tests and confirm GREEN.

## Task 7: TED CLI commands

**Files:**
- Modify: `src/opentradeintel/cli.py`
- Modify: `tests/integration/test_cli.py`

1. Write failing CLI tests using an injected service boundary for `ted search`, JSON output, output-file JSON, validation errors, `ted match`, and no-traceback connector errors.
2. Run focused CLI tests and confirm RED.
3. Add the `ted` Typer group and shared query/output helpers without TED field or matcher logic in CLI functions.
4. Run focused tests and confirm GREEN.

## Task 8: Optional live smoke test

**Files:**
- Create: `tests/live/test_ted_live.py`
- Modify: `pyproject.toml`
- Modify: `.github/workflows/ci.yml`

1. Register a strict `live` marker and exclude it from default test runs.
2. Add one bounded official public query asserting only the connector's public contract.
3. Verify `uv run pytest` deselects the live test and `uv run pytest -m live tests/live` executes it locally.

## Task 9: Synthetic matcher benchmark

**Files:**
- Create: `benchmarks/dataset.json`
- Create: `benchmarks/run.py`
- Create: `tests/unit/test_benchmark.py`
- Create: `docs/benchmark.md`

1. Create 30 synthetic products, 20 synthetic opportunities, and hand-authored relevance labels covering positive, negative, ambiguous, certification, market, MOQ, and category cases.
2. Write failing tests for dataset minimums, deterministic metrics, and machine-readable result structure.
3. Implement the runner and compute precision@1, precision@3, MRR, false positives, and false negatives.
4. Run the benchmark twice and verify byte-for-byte stable output.
5. Record the actual baseline and known failure modes in `docs/benchmark.md`.

## Task 10: Documentation and contributor path

**Files:**
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `docs/connectors.md`
- Modify: `docs/architecture.md`
- Modify: `docs/development.md`
- Modify: `ROADMAP.md`
- Modify: `CHANGELOG.md`
- Modify: `examples/README.md`
- Create: `examples/connectors/minimal.py`

1. Add an honest 30-second TED quick start and direct match flow.
2. Document connector boundaries, official-source requirements, fixture tests, and a minimal connector example.
3. Distinguish public TED snapshots from all synthetic catalogs and benchmark records.
4. Document limitations and deferred features without unsupported claims.

## Task 11: Version and secure release workflow

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/opentradeintel/__init__.py`
- Modify: `tests/unit/test_models.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/security.yml`
- Create: `.github/workflows/publish.yml`
- Modify: `.github/dependabot.yml` if needed
- Modify: `docs/development.md`
- Modify: `uv.lock`

1. Resolve immutable SHAs for every referenced GitHub Action from its official repository and retain version comments.
2. Pin CI, CodeQL, artifact, uv, and PyPI publish actions; preserve least-privilege permissions.
3. Add build/check and PyPI OIDC publish jobs with the `pypi` environment, job-scoped `id-token: write`, and attestations.
4. Update the package to `0.2.0` only after the additive semver assessment is documented.
5. Refresh and check the lockfile; build wheel/sdist and inspect package contents.
6. Record the exact pending-publisher values that the user must configure in PyPI before release.

## Task 12: Repository protection feasibility

**External scope:** repository `b2baitrade-ui/opentradeintel` only

1. Read current branch protection/rulesets and authenticated user's repository role.
2. Determine exact CI/CodeQL check contexts from successful runs.
3. Prefer a main ruleset that requires PRs and checks, blocks force pushes/deletion, and grants repository-admin bypass to avoid locking out the sole maintainer.
4. Apply only if the API/plan supports that exact safe configuration; immediately read it back and document it.
5. If unavailable, document the API/plan limitation and make no workaround.

## Task 13: Complete local verification

1. Run `uv lock --check`.
2. Run `uv run ruff check .`.
3. Run `uv run ruff format --check .`.
4. Run `uv run mypy src tests benchmarks`.
5. Run `uv run pytest` and the optional live smoke separately.
6. Run `uv run python benchmarks/run.py` twice and compare output.
7. Run `uv build` and package metadata/content checks.
8. Run `docker build -t opentradeintel:0.2.0 .` and a container CLI smoke test.
9. Run a secret scan over the branch diff and repository history using an available scanner.
10. Inspect `git diff --check`, status, and the complete diff.

## Task 14: PR, CI, merge, and release gate

1. Commit coherent implementation changes on `feat/ted-connector` and push the branch.
2. Create PR `feat: add official TED public procurement connector` with What, Why, Architecture, official source, Testing, Benchmark, Security/privacy, and Backward compatibility sections.
3. Wait for every CI and CodeQL check to complete successfully; fix failures on the feature branch.
4. Stop and request the required PyPI pending Trusted Publisher/environment UI action before anything that would trigger publication.
5. Once the user confirms PyPI setup, merge normally without self-approval.
6. Wait for green `main`, tag/release `v0.2.0`, and wait for the publish workflow.
7. Verify the GitHub release, PyPI project, installed wheel CLI, and final repository status.
