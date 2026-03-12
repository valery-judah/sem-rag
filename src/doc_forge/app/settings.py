"""Internal runtime settings for the upload app."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    """Environment-backed runtime configuration."""

    database_url: str
    artifact_root: Path
    service_name: str
    environment: str
    log_level: str
    embedding_backend: str
    embedding_model_name: str
    answer_generator_backend: str
    answer_generator_model_name: str
    answer_generator_max_new_tokens: int
    answer_generator_temperature: float


def load_settings() -> AppSettings:
    """Load app settings from the process environment."""

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set")

    artifact_root = Path(os.environ.get("DOC_FORGE_ARTIFACT_ROOT", "data")).resolve()
    return AppSettings(
        database_url=database_url,
        artifact_root=artifact_root,
        service_name=os.environ.get("DOC_FORGE_SERVICE_NAME", "doc_forge-api"),
        environment=os.environ.get("DOC_FORGE_ENVIRONMENT", "dev"),
        log_level=os.environ.get("DOC_FORGE_LOG_LEVEL", "INFO"),
        embedding_backend=os.environ.get("DOC_FORGE_EMBEDDING_BACKEND", "deterministic"),
        embedding_model_name=os.environ.get(
            "DOC_FORGE_EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        ),
        answer_generator_backend=os.environ.get(
            "DOC_FORGE_ANSWER_GENERATOR_BACKEND",
            "deterministic",
        ),
        answer_generator_model_name=os.environ.get(
            "DOC_FORGE_ANSWER_GENERATOR_MODEL",
            "mlx-community/TinyLlama-1.1B-Chat-v1.0",
        ),
        answer_generator_max_new_tokens=int(
            os.environ.get("DOC_FORGE_ANSWER_GENERATOR_MAX_NEW_TOKENS", "256")
        ),
        answer_generator_temperature=float(
            os.environ.get("DOC_FORGE_ANSWER_GENERATOR_TEMPERATURE", "0.0")
        ),
    )
