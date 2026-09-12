# ---- uv binary (avoids pip in the build stage) ----
FROM ghcr.io/astral-sh/uv:latest AS uv

# ---- build stage ----
FROM python:3.12-slim AS builder

WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_COMPILE_BYTECODE=1
COPY --from=uv /uv /usr/bin/uv

# Dependencies first -> cached layer, invalidated only when the lock changes
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/
RUN uv sync --frozen --no-dev

# ---- runtime stage ----
FROM python:3.12-slim AS runtime

# Non-root user
RUN groupadd --system --gid 1001 app \
    && useradd --system --uid 1001 --gid app --create-home app

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/src /app/src

USER app
EXPOSE 8000
ENTRYPOINT ["python", "-m", "uvicorn", "src.acestream_proxy.main:app", "--host", "0.0.0.0", "--port", "8000"]
