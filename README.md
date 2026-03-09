# parity

Minimal question-answering MVP scaffold for a user-provided document corpus.

The current codebase is intentionally small. Today it exposes:

- `src/parity/retrieval.py`: an in-memory `SemanticIndex` demo
- `src/parity/cli.py`: a CLI that runs the retrieval demo

The product target is broader than the current implementation. The product north star lives in `docs/evergreen/mvp.md`, which defines the MVP scope for question answering over a bounded PDF and Markdown corpus with inspectable evidence. Supporting delivery and workflow material may exist in `docs/delivery/`, but it is not the canonical scope definition.

## Read First

- `AGENTS.md`: repo workflow entry point for agents
- `docs/evergreen/mvp.md`: MVP product north star and scope boundary
- `docs/evergreen/architecture.md`: current-state vs target-state architecture
- `docs/evergreen/api-contracts.md`: stable interfaces that exist today
- `docs/README.md`: documentation map

## Current Repository Shape

- `src/parity/__init__.py`: package export surface
- `src/parity/retrieval.py`: retrieval demo logic
- `src/parity/cli.py`: demo CLI entry point
- `docs/evergreen/`: durable canonical product and repo documentation
- `docs/delivery/`: planning, architecture, and workflow drafts retained for reference; not the product north star
- `docs/workstreams/`: optional time-scoped execution records
- `docs/adrs/`: durable architectural decisions when needed
- `docs/harness/`: documentation tooling and templates

The repo does not currently implement document upload, PDF/Markdown ingestion, structure recovery, or grounded answer generation. Those capabilities are target MVP behavior, not present runtime behavior.

## Quickstart

```bash
make sync
make install
make run
```

Common validation targets from `Makefile`:

```bash
make fmt
make lint
make type
make test
```

## Repository Map

```text
AGENTS.md
docs/
  README.md
  delivery/
  evergreen/
    mvp.md
    api-contracts.md
    architecture.md
    runbook.md
  workstreams/
  adrs/
  harness/
src/parity/
  __init__.py
  cli.py
  retrieval.py
```
