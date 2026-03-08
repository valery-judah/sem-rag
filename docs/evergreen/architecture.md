# Architecture

## Purpose
This file captures stable architectural truth for `docforge`. Use it when you need the current high-level shape of the system, not the execution history of a single effort.

## When To Use
- Starting work on a subsystem
- Explaining repo boundaries to a new contributor
- Checking whether a proposed change should become an ADR

## System Overview
`docforge` is a semantic-pipeline MVP that turns raw source documents into normalized, queryable artifacts. The repo currently contains source connectors, canonical and PDF-hybrid parsing flows, segmentation work, and a lightweight retrieval demo.

## Major Components
- Connectors in `src/docforge/connectors/` fetch source content and metadata.
- Parsers in `src/docforge/parsers/` normalize content into canonical text and structure.
- PDF-hybrid parsing in `src/docforge/parsers/pdf_hybrid/` handles PDF-specific extraction and distillation paths.
- Segmentation and retrieval surfaces prepare parsed content for search and demo querying.
- Tests in `tests/` cover connectors, parsers, retrieval, and supporting developer tooling.

## Boundaries And Dependencies
- Connectors fetch and package raw documents; they do not own parsing policy.
- Parsers produce canonical document structure; they do not own retrieval behavior.
- PDF-hybrid code is a parser subsystem, not a separate product surface.
- Retrieval consumes parser outputs and should stay decoupled from connector details.
- Feature-level contracts and implementation notes currently live in `docs/workstreams/`.

## Known Constraints
- The current repo is an MVP, so some planned pipeline stages exist only as docs.
- Durable architecture belongs here or in ADRs, not in workstream notes.
- Existing `docs/workstreams/` material remains the current source for many workstream-specific contracts.

## Related Docs
- ADRs: `docs/adrs/`
- Active execution history: `docs/workstreams/`
- Harness conventions: `docs/harness/`
