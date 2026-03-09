# WS-001 Status

**Status:** active  
**Last updated:** 2026-03-09

## Current State

- `contract-lock.md` is the canonical Phase 1 contract artifact for WS-001.
- `src/parity/_contracts/` contains the internal shared schema layer for the locked Phase 1 objects.
- `tests/test_contracts.py` validates field requirements, enums, answer-status semantics, and lifecycle transitions.
- `tests/test_contract_seam.py` validates the supported-answer seam, insufficient-evidence seam, and lifecycle seam over in-memory fixtures.

## Locked Now

- Internal shared models: `Document`, `Section`, `Chunk`, `SourceReference`, `RetrievalHit`, and `Answer`
- Phase 1 answer statuses: `supported` and `insufficient_evidence`
- Minimum inspectable provenance for a `SourceReference`: `doc_id`, `document_title`, and `snippet`
- `insufficient_evidence` answers must include `answer_text`, `insufficiency_note`, and `source_references=[]`
- Processing status set and allowed transitions through `ready`, with `failed` allowed from any in-progress state
- WS-001 scope boundary: no public API design, parser heuristic lock, retrieval tuning, or prompt tuning

## Deferred Within MVP

- PDF heading inference heuristics
- Markdown normalization heuristics
- Chunk sizing and overlap policy
- Retrieval thresholds and ranking defaults
- Prompt wording and answer style
- Product-facing confidence exposure

## Deferred Beyond MVP

- OCR
- Table, figure, and image understanding
- Hybrid or lexical-first retrieval
- Advanced reranking pipelines
- Release-gate policy and production observability hardening

## Validation Evidence

- Contract model validation lives in `tests/test_contracts.py`
- Fixture-driven seam validation lives in `tests/test_contract_seam.py`
- Repository checks for this workstream remain `make fmt`, `make lint`, `make type`, and `make test`
