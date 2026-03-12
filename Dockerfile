# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_CACHE_DIR=/tmp/.uv-cache \
    PARITY_ARTIFACT_ROOT=/artifacts

WORKDIR /app

COPY pyproject.toml uv.lock README.md alembic.ini ./

RUN --mount=type=cache,target=/tmp/.uv-cache \
    uv sync --frozen --no-dev --no-install-project --group llm

COPY src ./src

RUN --mount=type=cache,target=/tmp/.uv-cache \
    uv sync --frozen --no-dev --group llm

ENV PATH="/app/.venv/bin:${PATH}"

RUN groupadd --system --gid 1000 parity \
    && useradd --system --uid 1000 --gid 1000 --create-home --home-dir /home/parity parity \
    && install -d --owner=parity --group=parity /artifacts

USER parity

EXPOSE 8000

ENTRYPOINT ["python", "-m", "parity.runtime"]
CMD ["api"]
