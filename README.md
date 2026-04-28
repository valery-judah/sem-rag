# doc_forge

Minimal question-answering MVP scaffold for a user-provided document corpus.

The product target is broader than the current implementation. The product north star lives in `docs/evergreen/mvp.md`, which defines the MVP scope for question answering over a bounded PDF and Markdown corpus with inspectable evidence. Supporting delivery and workflow material may exist in `docs/delivery/`, but it is not the canonical scope definition.

## Read First

- `AGENTS.md`: repo workflow entry point for agents
- `docs/evergreen/mvp.md`: MVP product north star and scope boundary
- `docs/evergreen/architecture.md`: current-state vs target-state architecture
- `docs/evergreen/api-contracts.md`: stable interfaces that exist today (includes API examples)
- `docs/evergreen/runbook.md`: local operations and troubleshooting
- `docs/evergreen/manual-e2e.md`: step-by-step manual end-to-end ingestion test
- `docs/README.md`: documentation map

## Current Repository Shape

- `src/doc_forge/`: internal runtime code for lifecycle, query, persistence, evaluation, and devtools
- `e2e/`: docker-backed end-to-end and smoke scenarios plus shared runtime and evaluation helpers
- `evals/`: authored evaluation corpora, case sets, and related schemas used by the evaluation subsystem
- `docs/evergreen/`: durable canonical product and repo documentation
- `docs/delivery/`: planning, architecture, and workflow drafts retained for reference; not the product north star
- `docs/workstreams/`: optional time-scoped execution records
- `docs/adrs/`: durable architectural decisions when needed

## E2E And Evaluation Subsystems

- `src/doc_forge/evaluation/`: internal evaluation subsystem for authored answer-layer cases, identifiers, and evaluation logic
- `e2e/`: docker-backed subsystem for end-to-end runtime coverage, query smokes, authored eval smokes, and shared test drivers
- `evals/`: repository data for evaluation runs, including committed corpora and authored case storage under `evals/cases/`
- `tests/evaluation/`: focused unit coverage for evaluation helpers and answer-layer behavior

## Quickstart

Start the local Docker stack (requires Postgres DB):
```bash
make docker-up-build
```

Then prepare the environment:
```bash
uv sync
```

The API and worker are blocking processes and should be run in separate terminals (or in the background):
```bash
# Terminal 1
uv run poe run-api

# Terminal 2
uv run poe run-worker
```

With those running, you can execute the end-to-end tests in another terminal:
```bash
# Terminal 3
uv run poe test-e2e
```

## Command Model

- Use `uv run poe <task>` for Python developer tasks such as formatting, linting, type checking, tests, migrations, and local app commands.
- Use `make <target>` for Docker, Compose, observability, and other local DevEx wrappers.
- Host-side `uv` commands use the repo-local cache configured in `uv.toml` at `./.tmp_uv_cache`.

Python developer tasks run through Poe:

```bash
uv run poe fmt
uv run poe fmt-check
uv run poe lint
uv run poe type
uv run poe test
uv run poe clean --dry-run
uv run poe verify
```

Local DevEx and infrastructure wrappers stay in `Makefile`:

```bash
make docker-up-build
make docker-log-index
make observability-up-build
make observability-down
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
    manual-e2e.md
  workstreams/
  adrs/
  harness/
e2e/
evals/
src/doc_forge/
  __init__.py
  evaluation/
```
