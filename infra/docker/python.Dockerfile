# syntax=docker/dockerfile:1.7
# One image for the API, the workers and migrations (same code, different command).

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
RUN groupadd --gid 10001 axiomq && useradd --uid 10001 --gid axiomq --create-home axiomq

FROM base AS uv
RUN pip install --no-cache-dir "uv==0.8.17"
WORKDIR /app

# ---- dev: editable install + dev tools; source is bind-mounted by docker compose -------------
FROM uv AS dev
COPY pyproject.toml uv.lock ./
COPY quant_engine/pyproject.toml quant_engine/
COPY backend/pyproject.toml backend/
COPY workers/pyproject.toml workers/
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-install-workspace
COPY quant_engine quant_engine
COPY backend backend
COPY workers workers
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen
ENV PATH=/app/.venv/bin:$PATH
WORKDIR /app/backend

# ---- build: non-editable, no dev dependencies --------------------------------------------------
FROM uv AS build
COPY pyproject.toml uv.lock ./
COPY quant_engine/pyproject.toml quant_engine/
COPY backend/pyproject.toml backend/
COPY workers/pyproject.toml workers/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-workspace --package axiomq-workers
COPY quant_engine quant_engine
COPY backend backend
COPY workers workers
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --package axiomq-workers

# ---- runtime: only the virtualenv and migration files, running as non-root ---------------------
FROM base AS runtime
WORKDIR /app
COPY --from=build --chown=root:root /app/.venv /app/.venv
COPY --from=build --chown=root:root /app/backend/alembic.ini /app/backend/alembic.ini
COPY --from=build --chown=root:root /app/backend/migrations /app/backend/migrations
ENV PATH=/app/.venv/bin:$PATH
WORKDIR /app/backend
USER axiomq
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"
CMD ["uvicorn", "axiomq_api.asgi:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--no-server-header"]
