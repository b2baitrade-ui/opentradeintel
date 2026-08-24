.PHONY: install lint format format-check typecheck test benchmark check run

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

test:
	uv run pytest

benchmark:
	uv run python benchmarks/run.py

check: lint format-check typecheck test benchmark

run:
	uv run uvicorn opentradeintel.api.app:app --host 0.0.0.0 --port 8000
