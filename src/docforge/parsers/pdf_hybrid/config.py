from pydantic import BaseModel, Field


class SelectionWeights(BaseModel):
    w_chars: float = 1.0
    w_blocks: float = 0.2
    w_dupes: float = 2.0
    w_coords: float = 0.3
    w_headings: float = 0.2
    w_assets: float = 0.1


class PdfHybridConfig(BaseModel):
    marker_timeout_s: int = 120
    mineru_timeout_s: int = 180
    selection_weights: SelectionWeights = Field(default_factory=SelectionWeights)
    # Rollback/mitigation config:
    # "marker", "mineru", or None for normal hybrid
    force_engine: str | None = None
    emit_artifacts: bool = True
    artifact_dir: str | None = None
