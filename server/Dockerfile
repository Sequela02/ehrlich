FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN uv sync --no-dev --no-install-project
COPY src/ src/
RUN uv sync --no-dev

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "ehrlich.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
