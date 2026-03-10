# Architecture

**Status:** Verified
**Last verified:** 2026-03-08

## Purpose
This file captures the current architectural truth for `parity` and the gap between today's code and the target product described in [`docs/evergreen/mvp.md`](./mvp.md). Use it when you need the current repo shape, want to avoid overstating implementation status, or need to decide whether a planned capability is already present.

## When To Use
- Starting work on a subsystem
- Explaining repo boundaries to a new contributor
- Checking whether a proposal belongs in evergreen docs, a workstream, or an ADR

## Read Next
- `docs/evergreen/mvp.md`: Canonical. Product north star and scope boundary.
- `docs/evergreen/api-contracts.md`: Canonical. Stable runtime interfaces that exist today.
- `docs/evergreen/runbook.md`: Canonical. Local operation guidance and standard commands.
- `docs/README.md`: Canonical. Docs index and task-based routes.

## Current System Shape
The repository currently exposes a lightweight package plus documentation scaffolding:

- `src/parity/retrieval.py`: in-memory semantic-like retrieval over tokenized text
- `src/parity/cli.py`: demo entry point that builds a small hard-coded corpus and prints ranked matches
- `src/parity/__init__.py`: package export surface
- `docs/evergreen/`: durable product and repo documentation
- `docs/workstreams/` and `docs/adrs/`: documentation structure for future execution records and long-lived decisions
- `docs/harness/`: docs tooling, templates, and playbooks

Today there is no implemented ingestion pipeline, parser subsystem, PDF/Markdown normalization flow, answer-generation layer, or source-grounded citation/navigation surface.

## Current Runtime Boundary
The runtime boundary that exists today is intentionally narrow:

- `parity.SemanticIndex` accepts a non-empty `list[str]`
- `SemanticIndex.search(query, k=3)` returns ranked `(document_text, score)` tuples
- `python -m parity.cli` and `make run` exercise that demo surface

This is a retrieval demonstration, not the full MVP service.

## Target State From The MVP Doc
[`docs/evergreen/mvp.md`](./mvp.md) is the target product definition, not a statement of current implementation. It describes a service that should eventually:

- ingest user-uploaded PDF and Markdown documents
- normalize them into a unified internal corpus
- retrieve relevant content across documents
- answer questions using retrieved evidence
- return source references that let the user inspect supporting material

Those capabilities should be treated as planned work until corresponding code exists.

## Architectural Guidance
Keep the current docs and code honest about the gap between demo and target product:

1. Do not document PDF/Markdown ingestion, parsing, or grounded answering as implemented behavior unless code exists for it.
2. Keep retrieval-demo behavior decoupled from future ingestion/parsing contracts until those surfaces are introduced intentionally.
3. Use workstreams for time-scoped design and execution notes; promote only durable, implemented truths into evergreen docs.
4. Use ADRs only for decisions that outlive a single workstream or materially constrain future MVP implementation.

## Documentation Authority
- `docs/evergreen/mvp.md` is the product north star.
- This file describes the current repo shape and the gap to that north star.
- `docs/evergreen/api-contracts.md` describes stable interfaces that are implemented today.
- `docs/README.md` routes contributors through the documentation system.
- `docs/workstreams/` and `docs/adrs/` are available structure, but may be empty between efforts.
