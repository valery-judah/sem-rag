FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PARITY_ARTIFACT_ROOT=/artifacts

WORKDIR /app

COPY pyproject.toml uv.lock README.md alembic.ini ./
COPY src ./src

RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 8000

ENTRYPOINT ["python", "-m", "parity.runtime"]
CMD ["api"]
