# Design: PR4 - Intermediate Schema + Artifact Emission

## 1. Context and Scope

This document outlines the design for PR4 of the Hybrid PDF Parsing Pipeline, addressing the requirements from `01_rfc.md §9` and `04_workplan.md`.

**Scope:**
- Define the intermediate schema (`ExtractedPdfDocument`) mapping exactly to the RFC.
- Implement artifact emission logic for writing `extracted_pdf_document.json` and `selection_log.jsonl`.
- Add configuration to enable/disable artifact emission safely.

**Touched Modules:**
- `src/docforge/parsers/pdf_hybrid/schema.py` (New)
- `src/docforge/parsers/pdf_hybrid/artifacts.py` (New)
- `src/docforge/parsers/pdf_hybrid/config.py` (Update)

---

## 2. Schema Classes (`schema.py`)

We will introduce Pydantic models in `src/docforge/parsers/pdf_hybrid/schema.py` to represent the intermediate schema. These models will reuse `BlockCandidate` and `AssetCandidate` from `models.py`.

```python
from typing import Any
from pydantic import BaseModel, Field
from .models import BlockCandidate, AssetCandidate

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
```

---

## 3. Artifact Logging (`artifacts.py`)

Artifact emission should be deterministic and stateless. We will introduce logging functions and a specific Pydantic model for the `jsonl` logs.

### 3.1 Selection Log Entry
```python
class SelectionLogEntry(BaseModel):
    page_idx: int
    selected_engine: str | None
    reason: str
    scores: dict[str, float]
    statuses: dict[str, str]
    signals: dict[str, dict[str, Any]]
```

### 3.2 Emission Functions
```python
from pathlib import Path
from .schema import ExtractedPdfDocument
from .selection import SelectionResult, score_candidate
from .models import PageCandidate
from .config import PdfHybridConfig

def build_selection_log(
    all_candidates: dict[int, dict[str, PageCandidate]],
    selection_results: dict[int, SelectionResult],
    config: PdfHybridConfig
) -> list[SelectionLogEntry]:
    """
    Constructs log entries detailing why engines were selected per page.
    (Recomputes scores via score_candidate for detailed logging).
    """
    pass

def write_selection_log(log: list[SelectionLogEntry], path: Path) -> None:
    """
    Writes the selection log as JSONL to the given path.
    """
    pass

def write_extracted_document(doc: ExtractedPdfDocument, path: Path) -> None:
    """
    Writes the ExtractedPdfDocument schema as pretty JSON.
    """
    pass
```

---

## 4. Configuration Update (`config.py`)

To satisfy the rollback/mitigation requirement (allowing disabling of intermediate emission for storage constraints), update `PdfHybridConfig`:

```python
class PdfHybridConfig(BaseModel):
    # existing fields...
    marker_timeout_s: int = 120
    mineru_timeout_s: int = 180
    selection_weights: SelectionWeights = Field(default_factory=SelectionWeights)
    force_engine: str | None = None
    
    # New fields for PR4
    emit_artifacts: bool = True
    artifact_dir: str | None = None
```

---

## 5. Testing Strategy

1. **Schema Validation Tests:**
   - Unit tests to ensure `ExtractedPdfDocument.model_validate_json(doc.model_dump_json())` roundtrips perfectly.
   - Verify that optional properties fall back correctly.

2. **Artifact Determinism (Snapshot Tests):**
   - In `tests/parsers/pdf_hybrid/test_artifacts.py`.
   - Create a static `ExtractedPdfDocument` mock and dummy candidates.
   - Invoke `build_selection_log`, `write_selection_log`, and `write_extracted_document` to a temporary directory.
   - Assert the outputs precisely match a static string/file snapshot checked into the repository.
   - Validates that artifact layout, file naming (`extracted_pdf_document.json`, `selection_log.jsonl`), and formatting remain completely stable across commits.

## 6. Definition of Done
- `schema.py` precisely matches RFC §9.
- `artifacts.py` accurately emits `extracted_pdf_document.json` and `selection_log.jsonl`.
- `PdfHybridConfig` supports toggle and directory config.
- Snapshot tests guarantee format determinism.
- `make fmt`, `make lint`, `make type`, `make test` pass.
