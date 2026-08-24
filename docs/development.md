# Development guide

## Requirements

- Python 3.12, 3.13, or 3.14.
- `uv` for dependency and environment management.
- Docker for container verification (optional for ordinary unit work).
- GNU Make only if you want shorthand commands; it is not required on Windows.

## Setup

```bash
uv sync --all-groups --locked
uv run pre-commit install
```

The project is tested locally on Python 3.14.5 and in CI across the supported Python matrix.

## Test-first workflow

For behavior changes, write one focused test, run it and confirm it fails for the missing behavior, implement the smallest change, then run the focused and accumulated suites. Tests should assert observable behavior with hand-derived expectations and avoid mocks unless a real external boundary makes one necessary.

## Quality commands

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests benchmarks examples
uv run vulture src --min-confidence 90 --ignore-names cls
uv run pytest --cov=opentradeintel --cov-report=term-missing --cov-fail-under=90
uv run python benchmarks/run.py
uv run pip-audit
uv lock --check
```

On systems with GNU Make:

```bash
make install
make lint
make format
make typecheck
make deadcode
make test
make audit
make check
```

## Running interfaces

```bash
uv run opentradeintel --help
uv run opentradeintel match --tender examples/tenders/sample.json --catalog examples/catalogs/sample.csv
uv run opentradeintel ted search --query "dried fruit" --limit 1
uv run opentradeintel ted match --query "dried fruit" --catalog examples/catalogs/sample.csv
uv run uvicorn opentradeintel.api.app:app --reload
```

Default pytest runs exclude the external `live` marker. To run the one bounded public TED smoke test explicitly:

```bash
uv run pytest -m live tests/live
```

## Docker verification

```bash
docker compose config
docker compose build
docker compose up -d
curl http://127.0.0.1:8000/health
docker compose down
```

## Release process

1. Update version and changelog.
2. Run every local quality gate and secret scan.
3. Commit and push without force.
4. Wait for the actual GitHub CI run to succeed.
5. Confirm the PyPI `pypi` environment and pending Trusted Publisher are configured as documented in `docs/distribution.md`.
6. Create the version tag and GitHub release only from the verified commit.
7. Let the release workflow build and publish through OIDC; never add a long-lived PyPI token.

See `CONTRIBUTING.md` for branch, parser, connector, privacy, and pull-request guidance.
