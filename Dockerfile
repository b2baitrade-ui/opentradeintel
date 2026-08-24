# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.12.2 AS uv

FROM python:3.12-slim AS builder
COPY --from=uv /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY README.md LICENSE ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim AS runtime
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN addgroup --system opentradeintel \
    && adduser --system --ingroup opentradeintel --home /nonexistent --no-create-home opentradeintel
WORKDIR /app
COPY --from=builder --chown=opentradeintel:opentradeintel /app/.venv /app/.venv
USER opentradeintel
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["uvicorn", "opentradeintel.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
