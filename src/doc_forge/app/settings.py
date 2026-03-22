"""Environment-backed runtime configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRETS_DIR = Path("/run/secrets")


class Settings(BaseSettings):
    """Typed, validated runtime configuration.

    All fields are read from environment variables prefixed with ``DOC_FORGE_``
    (e.g. ``DOC_FORGE_LOG_LEVEL``).  ``.env`` is loaded as a local convenience;
    production config should be injected via env vars or secret files.
    """

    model_config = SettingsConfigDict(
        env_prefix="DOC_FORGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        secrets_dir=DEFAULT_SECRETS_DIR if DEFAULT_SECRETS_DIR.is_dir() else None,
    )

    environment: Literal["dev", "test", "prod"] = "prod"
    service_name: str = "doc_forge-api"
    log_level: str = "INFO"
    enable_swagger: bool = False
    port: int = Field(default=8000)
    auto_migrate: bool = False
    worker_poll_seconds: float = 0.25

    # DATABASE_URL is unprefixed by convention (Alembic, PaaS platforms).
    database_url: str = Field(
        default="postgresql+psycopg://doc-forge:doc-forge@localhost:5432/doc-forge",
        validation_alias="DATABASE_URL",
    )
    artifact_root: Path = Field(default=Path("data"))

    embedding_backend: str = "deterministic"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    answer_generator_backend: str = "deterministic"
    answer_generator_model: str = "mlx-community/TinyLlama-1.1B-Chat-v1.0"
    answer_generator_max_new_tokens: int = 256
    answer_generator_temperature: float = 0.0

    @property
    def docs_enabled(self) -> bool:
        return self.enable_swagger

    @field_validator("artifact_root", mode="after")
    @classmethod
    def resolve_artifact_root(cls, v: Path) -> Path:
        return v.resolve()


@lru_cache
def get_settings() -> Settings:
    """Load and cache process-scoped runtime settings."""
    return Settings()
