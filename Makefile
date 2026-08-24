.PHONY: install lint format format-check typecheck deadcode test benchmark audit check run

install:
	uv sync --all-groups --locked

lint:
	uv run ruff check .

format:
	uv run ruff check --fix .
	uv run ruff format .

format-check:
	uv run ruff format --check .

typecheck:
	uv run mypy src tests benchmarks examples

deadcode:
	uv run vulture src --min-confidence 90 --ignore-names cls

test:
	uv run pytest --cov=opentradeintel --cov-report=term-missing --cov-fail-under=90

benchmark:
	uv run python benchmarks/run.py

audit:
	uv run pip-audit

check: lint format-check typecheck deadcode test benchmark audit

run:
	uv run uvicorn opentradeintel.api.app:app --host 0.0.0.0 --port 8000
