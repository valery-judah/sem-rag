"""Storage-facing artifact payloads used by the lifecycle runtime."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from doc_forge.corpus import SourceType


class RawArtifactRef(BaseModel):
    """Managed reference to a raw uploaded source artifact."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: str
    doc_id: str
    source_type: SourceType
    relative_path: str


class ExtractedArtifactBlock(BaseModel):
    """One ordered extractable block recovered from a source artifact."""

    model_config = ConfigDict(extra="forbid")

    kind: str = "text"
    text: str
    order_index: int = Field(ge=0)
    source_start_offset: int | None = Field(default=None, ge=0)
    source_end_offset: int | None = Field(default=None, ge=0)
    meta: dict[str, str] | None = None

    @model_validator(mode="after")
    def validate_offsets(self) -> ExtractedArtifactBlock:
        if (
            self.source_start_offset is not None
            and self.source_end_offset is not None
            and self.source_end_offset < self.source_start_offset
        ):
            raise ValueError(
                "source_end_offset must be greater than or equal to source_start_offset",
            )
        return self


class ExtractedArtifactPage(BaseModel):
    """Ordered extractable blocks for one source page."""

    model_config = ConfigDict(extra="forbid")

    page_number: int = Field(ge=1)
    blocks: list[ExtractedArtifactBlock] = Field(default_factory=list)


class ExtractedArtifact(BaseModel):
    """Inspectable extraction output persisted between lifecycle stages."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str
    source_type: SourceType
    extractor_version: str
    pages: list[ExtractedArtifactPage] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    meta: dict[str, str] | None = None


class NormalizedArtifactBlock(BaseModel):
    """One canonical normalized block used for downstream structure recovery."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    text: str
    order_index: int = Field(ge=0)
    heading_level: int | None = Field(default=None, ge=1)
    heading_path: list[str] = Field(default_factory=list)
    page_number: int | None = Field(default=None, ge=1)
    source_start_offset: int | None = Field(default=None, ge=0)
    source_end_offset: int | None = Field(default=None, ge=0)
    meta: dict[str, str] | None = None

    @model_validator(mode="after")
    def validate_offsets(self) -> NormalizedArtifactBlock:
        if (
            self.source_start_offset is not None
            and self.source_end_offset is not None
            and self.source_end_offset < self.source_start_offset
        ):
            raise ValueError(
                "source_end_offset must be greater than or equal to source_start_offset",
            )
        return self


class NormalizedArtifact(BaseModel):
    """Canonical normalized document payload persisted after extraction."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str
    source_type: SourceType
    normalizer_version: str
    blocks: list[NormalizedArtifactBlock] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)
