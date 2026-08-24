.PHONY: install lint format format-check typecheck test check run

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
	uv run mypy src tests

test:
	uv run pytest

check: lint format-check typecheck test

run:
	uv run uvicorn opentradeintel.api.app:app --host 0.0.0.0 --port 8000
