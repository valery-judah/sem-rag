FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_CACHE_DIR=/tmp/.uv-cache \
    PARITY_ARTIFACT_ROOT=/artifacts

WORKDIR /app

COPY pyproject.toml uv.lock README.md alembic.ini ./

RUN uv sync --frozen --no-dev --no-install-project \
    && rm -rf "${UV_CACHE_DIR}"

COPY src ./src

RUN uv sync --frozen --no-dev \
    && rm -rf "${UV_CACHE_DIR}"

ENV PATH="/app/.venv/bin:${PATH}"

RUN groupadd --system --gid 1000 parity \
    && useradd --system --uid 1000 --gid 1000 --create-home --home-dir /home/parity parity \
    && mkdir -p /artifacts \
    && chown -R parity:parity /app /artifacts

USER parity

EXPOSE 8000

ENTRYPOINT ["python", "-m", "parity.runtime"]
CMD ["api"]
