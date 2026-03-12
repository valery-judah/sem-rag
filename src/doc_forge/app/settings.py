"""Internal runtime settings for the upload app."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Environment-backed runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+psycopg://doc-forge:doc-forge@localhost:5432/doc-forge", 
        alias="DATABASE_URL"
    )
    artifact_root: Path = Field(default=Path("data"), alias="DOC_FORGE_ARTIFACT_ROOT")
    service_name: str = Field(default="doc_forge-api", alias="DOC_FORGE_SERVICE_NAME")
    environment: str = Field(default="prod", alias="DOC_FORGE_ENVIRONMENT")
    enable_swagger: bool = Field(default=False, alias="DOC_FORGE_ENABLE_SWAGGER")
    log_level: str = Field(default="INFO", alias="DOC_FORGE_LOG_LEVEL")
    embedding_backend: str = Field(default="deterministic", alias="DOC_FORGE_EMBEDDING_BACKEND")
    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", 
        alias="DOC_FORGE_EMBEDDING_MODEL"
    )
    answer_generator_backend: str = Field(default="deterministic", alias="DOC_FORGE_ANSWER_GENERATOR_BACKEND")
    answer_generator_model_name: str = Field(
        default="mlx-community/TinyLlama-1.1B-Chat-v1.0", 
        alias="DOC_FORGE_ANSWER_GENERATOR_MODEL"
    )
    answer_generator_max_new_tokens: int = Field(default=256, alias="DOC_FORGE_ANSWER_GENERATOR_MAX_NEW_TOKENS")
    answer_generator_temperature: float = Field(default=0.0, alias="DOC_FORGE_ANSWER_GENERATOR_TEMPERATURE")

    @field_validator("artifact_root", mode="after")
    @classmethod
    def resolve_artifact_root(cls, v: Path) -> Path:
        return v.resolve()


def load_settings() -> AppSettings:
    """Load app settings from the process environment."""
    return AppSettings()
