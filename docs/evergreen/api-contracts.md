# API Contracts

**Status:** Verified
**Last verified:** 2026-03-08

## Purpose
This document defines the stable interfaces that are actually implemented in the current `parity` package. It intentionally does not describe future ingestion, parsing, or answering contracts that are only present in the MVP doc.

The current runtime package name remains `parity`.

## Scope
### In Scope
- The Python surfaces exported by `src/parity/`
- The behavior of the current retrieval demo API
- Compatibility expectations for code that imports `parity.SemanticIndex`

### Out Of Scope
- Future document ingestion contracts
- Future PDF or Markdown parsing schemas
- Future retrieval-service request/response payloads
- Future answer-generation or citation interfaces
- Agent or harness workflow conventions

## Stable Interfaces
The stable package surface implemented today is:

- `parity.SemanticIndex`
- `parity.retrieval.SemanticIndex`

Both names refer to the same class exported from `src/parity/retrieval.py`.

### `SemanticIndex`
`SemanticIndex(documents: list[str])` constructs an in-memory retriever over a non-empty list of document strings.

Current constructor and method expectations:

- `documents` must be a non-empty `list[str]`
- empty document lists raise `ValueError`
- tokenization is internal implementation detail; callers should rely only on ranked retrieval behavior
- `search(query: str, k: int = 3) -> list[tuple[str, float]]`
- `k <= 0` raises `ValueError`
- results are sorted by descending score and truncated to at most `k` items
- each result tuple contains the original document string and a similarity score as `float`

### CLI Surface
`python -m parity.cli` and `make run` are stable local demo entrypoints for exercising the retrieval example, but they are not service APIs. The exact demo corpus may change without being treated as a contract break.

## Behavioral Guarantees
- `SemanticIndex` is in-memory only and does not persist state.
- Input documents are returned verbatim in search results; the API does not synthesize derived document identifiers or metadata.
- Similarity scores are implementation-dependent numeric outputs that support ranking; callers should not treat exact score values as a stable external scoring standard.
- The current package does not promise upload, parsing, chunking, citation, or grounded-answer behavior.

## Deferred Or Not Yet Stable
The following areas are intentionally not defined as evergreen service contracts yet:

- PDF ingestion and extraction contracts
- Markdown ingestion and structure contracts
- Corpus, section, or chunk schemas
- Answer-generation request/response shapes
- Source reference and citation payloads
- Any multi-document question-answering service interface beyond the demo retriever

## Compatibility And Change Control
- Prefer additive changes to stable contracts.
- Removing or renaming `SemanticIndex` from the package export surface is a breaking change.
- Changing the constructor or `search()` signature is a breaking change.
- Contract changes that affect downstream callers or tests must be recorded explicitly in docs.
- Future subsystem contracts should not be documented here until code implements them and the team intends downstream reliance on them.

## Relationship To Workstreams And ADRs
This file summarizes stable runtime interfaces that exist now.

- Design material for future ingestion, parsing, or answering layers belongs in workstreams until implemented and stabilized.
- Evergreen docs should absorb those contracts only after they become real package or service boundaries.
- Long-lived cross-cutting decisions should be promoted to ADRs only when they materially constrain the future MVP build.
