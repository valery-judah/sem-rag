# API Contracts

## Purpose
This document defines stable service-level contracts for the semantic-rag system. It covers the ingestion and parsing interfaces, normalized data shapes, and compatibility guarantees that downstream code, tests, and evergreen docs may rely on across workstreams.

The current runtime package name remains `docforge`. This file describes stable system contracts, not repository ergonomics.

## Scope
### In Scope
- Stable cross-subsystem contracts for ingestion and parsing
- Intentionally supported Python data models and interfaces
- Compatibility expectations for downstream callers and tests

### Out Of Scope
- Local developer convenience commands such as `make run`
- Repository layout details such as `src/docforge/`
- Agent or harness workflow conventions
- Provisional workstream experiments that are not yet promoted into evergreen docs

## Stable Interfaces
The current evergreen contract surface is type-centric rather than CLI-centric.

- `docforge.connectors.models.RawDocument` is the stable ingestion document shape.
- `docforge.connectors.base.BaseSourceConnector.fetch_documents(cursor)` is the stable connector boundary for incremental document fetch.
- `docforge.parsers.models.ParserConfig` is the stable parser configuration input shape.
- `docforge.parsers.models.ParsedDocument` is the stable canonical parser output shape.

The parser boundary is defined primarily by `RawDocument -> ParsedDocument`. Concrete parser classes may change so long as they preserve these contracts.

The following are not evergreen public APIs:
- `python -m docforge.cli` is a local demo entrypoint.
- `docforge.SemanticIndex` and `src/docforge/retrieval.py` are lightweight demo surfaces, not stable retrieval service contracts.
- `make run` is a developer convenience wrapper, not a service interface.

## Ingestion And Parsing Contracts
### Ingestion Input: `RawDocument`
Downstream parser code may rely on the following required fields on `RawDocument`:

- `doc_id`: stable document identity within the source domain
- `source`: source-system identifier
- `source_ref`: source-native reference or path
- `url`: source URL or source-like locator string
- `content_stream`: `Iterator[bytes]` for raw content bytes
- `content_type`: caller-declared content type for parser routing
- `metadata`: source and lineage metadata map
- `acl_scope`: access-control metadata map
- `timestamps`: source timestamp metadata map

The ingestion contract is raw-content oriented. Callers must not assume connector-specific parsing, normalization, or source-specific reshaping has already occurred.

### Connector Interface: `BaseSourceConnector.fetch_documents`
Connectors expose incremental fetch through `fetch_documents(cursor) -> Iterator[tuple[RawDocument, Any]]`.

Callers may rely on these interface expectations:
- each yielded item contains one valid `RawDocument` plus a cursor state representing progress up to that point
- connector outputs are intended for parser consumption, not direct retrieval use
- cursor semantics are connector-specific, but the yield shape is stable

### Parser Input: `ParserConfig`
`ParserConfig` is the stable parser behavior input shape. Evergreen callers may rely on:

- `parser_version` being required and non-empty
- parser behavior changing only through explicit config or parser-version changes
- configuration state being serializable and hashable for deterministic parser behavior

### Parser Output: `ParsedDocument`
Downstream consumers may rely on the following required top-level fields on `ParsedDocument`:

- `doc_id`
- `title`
- `canonical_text`
- `structure_tree`
- `anchors`
- `metadata`

`structure_tree` and `anchors` are part of the canonical parser contract, not separate public APIs. Their role is to provide stable document structure, section anchoring, and block anchoring subordinate to the `ParsedDocument` output.

### Parser Metadata And Invariants
The canonical parser contract guarantees:

- `metadata.parser_version` is present and non-empty
- `canonical_text` is non-empty when the output truthfully reports textual content
- block ranges in `structure_tree` and anchor ranges in `anchors.blocks` are valid and in bounds for `canonical_text`
- degraded outputs remain valid `ParsedDocument` instances rather than ad hoc failure payloads

The broader parser metadata contract, including `has_textual_content`, `anchor_completeness`, `degraded_output`, and `degraded_reason`, remains defined normatively by the parser RFC and is stable when promoted into canonical parser behavior.

## Behavioral Guarantees
- Parsers normalize raw connector output into canonical document structure and metadata suitable for downstream consumption.
- Downstream consumers must not depend on source-specific raw connector fields beyond the stable `RawDocument` contract.
- The parser prefers returning a valid degraded `ParsedDocument` over routine failure for unsupported or non-textual inputs.
- Determinism is part of the contract: the same raw content, parser config, and parser version should yield equivalent canonical parser output.
- Parser metadata must describe actual output state rather than aspirational parser state.

## Deferred Or Not Yet Stable
The following areas are intentionally not defined as evergreen service contracts yet:

- Chunking output schemas and provenance guarantees
- Retrieval request and response schemas
- Ranking or score semantics for retrieval consumers
- Agent-facing or harness-facing automation interfaces

These surfaces may exist as code, demos, or workstream design material, but they should be treated as provisional until intentionally stabilized.

## Compatibility And Change Control
- Prefer additive changes to stable contracts.
- Removing or renaming a stable field is a breaking change.
- Changing the meaning of a stable field is a breaking change.
- Contract changes that affect downstream callers or tests must be recorded explicitly in docs.
- Workstream RFCs may carry provisional or subsystem-local detail; evergreen docs should absorb only contracts intended for cross-workstream reliance.

## Relationship To Workstreams And ADRs
This file summarizes the stable semantic-rag contracts that are meant to survive individual workstreams.

- Workstream RFCs remain the authoritative home for provisional or subsystem-local contracts while an area is still evolving.
- Evergreen docs should be updated when a contract becomes stable enough for downstream reliance across workstreams.
- Long-lived cross-cutting contract decisions should also be promoted to ADRs when they materially affect multiple parts of the system.
