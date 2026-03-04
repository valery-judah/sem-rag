from typing import Any

from pydantic import BaseModel, Field

from .models import AssetCandidate, BlockCandidate


class SourcePdfInfo(BaseModel):
    content_hash: str
    page_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class PipelineInfo(BaseModel):
    pipeline_version: str
    config_hash: str


class EngineRunInfo(BaseModel):
    engine: str
    engine_version: str
    engine_config_hash: str
    engine_artifact_ref: str
    status: str


class ExtractedPage(BaseModel):
    page_idx: int
    width: float = 0.0
    height: float = 0.0
    selected_engine: str | None
    selection_reason: str
    blocks: list[BlockCandidate] = Field(default_factory=list)
    assets: list[AssetCandidate] = Field(default_factory=list)
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class ExtractedPdfDocument(BaseModel):
    doc_id: str
    source_pdf: SourcePdfInfo
    pipeline: PipelineInfo
    engine_runs: list[EngineRunInfo] = Field(default_factory=list)
    pages: list[ExtractedPage] = Field(default_factory=list)
