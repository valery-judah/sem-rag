# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**docforge** — a Python semantic RAG pipeline for document ingestion, parsing, segmentation, and retrieval. Built around strict Pydantic models with deterministic, anchor-based processing.

## Commands

All commands use `uv`. Prefer `make` targets:

```bash
make sync      # Install/sync dependencies
make install   # Editable install (required before tests)
make test      # Run pytest (depends on install)
make fmt       # Format + autofix (ruff)
make lint      # Lint check (ruff)
make type      # Type check (mypy, strict mode)
make check     # All checks: fmt + lint + type + test
make run       # Run CLI demo
```

Run a single test file: `uv run pytest tests/parsers/test_models.py -v`
Run a single test: `uv run pytest tests/parsers/test_models.py::test_name -v`

## Architecture

### Pipeline flow

```
Source Connectors → Parser → Segmentation → Retrieval
(RawDocument)    (ParsedDocument) (PassageSegment)  (SemanticIndex)
```

### Key layers (all in `src/docforge/`)

- **connectors/** — `BaseSourceConnector` ABC → `LocalFileConnector`. Produces `RawDocument` (Pydantic strict model with `content_stream: Iterator[bytes]`).
- **parsers/** — `BaseParser` ABC → `DeterministicParser`. Produces `ParsedDocument` with `canonical_text`, `structure_tree` (DocNode hierarchy), and `anchors` (AnchorMap).
  - `canonicalize.py` — HTML/Markdown/plain text normalization
  - `tree_builder.py` — Markdown → heading/block hierarchy
  - **pdf_hybrid/** — Multi-engine PDF extraction with fallback. Engines (Marker, MinerU) run in isolated venvs under `tools/`. Selection logic scores engines by char_count, block_count, coordinates, etc.
- **segmentation.py** — `segment_document()` produces `PassageSegment` list from block anchors with character offsets.
- **retrieval.py** — `SemanticIndex` bag-of-words baseline (demo only).

### Design invariants

- **Deterministic**: identical input → identical output
- **Anchored**: every segment references stable `BlockAnchor`/`SectionAnchor`
- **Strict validation**: Pydantic models enforce range bounds, non-empty fields, valid enums
- **Isolated tools**: heavy PDF engines (marker-pdf, mineru) live in separate venvs (`tools/marker/`, `tools/mineru/`), invoked via CLI subprocess wrappers

## Development Rules (from AGENTS.md)

- Use `uv` for all Python commands — never pip/poetry directly
- `src/` layout is source of truth; tests validate installed-package behavior (no path hacks)
- Use editable install (`make install`) before running tests
- Type annotations required for new/changed code
- Task matrix: docs-only → no tests needed; code change → `make test`; API/schema change → `make fmt lint type test`
- Keep `uv.lock` committed after dependency changes

## Testing

- Tests in `tests/`, mirroring `src/docforge/` structure
- Pytest with `-q` mode configured in pyproject.toml
- Uses parametrized tests, fixtures, and `pytest.raises` for validation errors
- PDF engine tests mock subprocess calls (no real PDF tools needed)

## Dependencies

- Python ≥ 3.11, build: hatchling
- Core: `pydantic>=2,<3`, `pypdf>=5.0.0`
- Dev: `ruff>=0.12.0`, `mypy>=1.17.0`, `pytest>=8.4.0`
- Ruff config: line-length 100, rules E/F/I/B/UP
