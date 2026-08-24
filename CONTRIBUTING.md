# Contributing to OpenTradeIntel

Thank you for helping build an open procurement and sourcing toolkit. Small, focused changes with clear tests are easiest to review.

## Local setup

Install Python 3.12 or newer and `uv`, then run:

```bash
git clone https://github.com/b2baitrade-ui/opentradeintel.git
cd opentradeintel
uv sync --all-groups --locked
uv run pre-commit install
```

The core workflow must continue to run without API keys or external services.

## Development workflow

1. Open or reference an issue for non-trivial behavior changes.
2. Create a short branch such as `feat/rss-parser`, `fix/csv-empty-values`, or `docs/matching-examples`.
3. Add a focused test that fails for the missing or broken behavior.
4. Implement the smallest cohesive change and keep the full suite green.
5. Update user-facing documentation and the changelog when appropriate.
6. Open a pull request using the repository template.

Do not commit real procurement records, supplier details, credentials, `.env` files, tokens, or generated customer data. Test fixtures and examples must be synthetic or redistributable under compatible terms with attribution.

## Quality gates

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests benchmarks examples
uv run vulture src --min-confidence 90 --ignore-names cls
uv run pytest --cov=opentradeintel --cov-report=term-missing --cov-fail-under=90
uv run python benchmarks/run.py
uv run pip-audit
```

`make check` runs the same commands on systems with GNU Make. Run `uv lock --check` after dependency changes. CI builds the production image and waits for its health check; Docker-related changes should also pass `docker compose config` and `docker compose build` locally.

## Add a public procurement connector

The smallest useful contribution path is one official, public, documented source:

1. Link the source owner's API documentation and terms in `docs/sources/`.
2. Keep HTTP acquisition, raw response validation, mapping, and application composition separate.
3. Map into the generic `Tender`; add only optional, source-neutral fields when the current model is insufficient.
4. Inject the HTTP client/transport and test every default path with complete offline fixtures.
5. Make any live test optional with `@pytest.mark.live`; CI must not depend on the source being online.
6. Document authentication, permissions, limits, pagination, timeout, and retry behavior. Do not add hidden retries.
7. Add CLI/API adapters only through a shared application service.

Local text sources implement `SourceConnector.read_text(Path) -> str`. Public APIs may use a capability-specific search client, as TED does, but must preserve the same acquisition -> mapping -> typed model boundary. See `examples/connectors/minimal.py` and `docs/connectors.md`.

Never use scraping when an official API provides the required data. Never add embedded credentials or silently upload source content.

## Adding a parser

Parsers convert raw content into `Tender` or `Product` models. Implement the appropriate protocol in `opentradeintel.parsers.base`, preserve useful source/record context in errors, and add representative valid and invalid fixtures. Register a file suffix in `parsers/loader.py` only when the parser is functional.

## Pull requests

Pull requests should explain the problem, approach, tests, privacy/security impact, and compatibility impact. Avoid unrelated formatting or refactoring. Maintainers may ask for a smaller scope or additional regression coverage.

By contributing, you agree that your contribution is licensed under Apache-2.0 and that you will follow the [Code of Conduct](CODE_OF_CONDUCT.md).
