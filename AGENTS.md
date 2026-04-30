# Agent Contract

sem-rag (Python package `doc_forge`) answers questions over a bounded corpus of uploaded PDF and
Markdown files and shows the evidence behind each answer. A FastAPI app and a lifecycle worker
share a Postgres database. Local runs use Docker Compose, and answer generation can use Ollama or
MLX.

## Canonical sources

### Repository and infrastructure
- `README.md` - project overview and quick start
- `docs/README.md` - docs index
- `docs/evergreen/runbook.md` - commands, local workflows, configuration, and troubleshooting
- `docs/evergreen/observability-operations.md` - the observability stack, log and query bundle locations, and eval run flows
- `docs/engineering/` - Python modeling, logging, and testing conventions
- `docs/harness/` - workstream templates, playbooks, and scripts

### Product and architecture
- `docs/evergreen/mvp.md` - product scope
- `docs/evergreen/functional-requirements.md` - MVP acceptance criteria
- `docs/evergreen/first-tier-failures.md` - critical failure model
- `docs/evergreen/architecture.md` - current architecture and the gap to the target
- `docs/evergreen/lifecycle-and-evidence-flow.md` - document and query lifecycles
- `docs/evergreen/retrieval-hierarchy.md` - retrieval units and provenance structure
- `docs/evergreen/api-contracts.md` - HTTP contract and local routes
- `docs/adrs/` - architecture decisions

`docs/evergreen/` is canonical and wins when sources disagree. `docs/delivery/` is reference only,
and `docs/workstreams/` is history only.

## Commands
- Use `make <target>` for repository workflows and `make help` for the current catalog. Pass extra arguments with `ARGS='...'`.
- Make calls Poe tasks in `poe_tasks.toml` for Python work and Docker Compose for containers. If no target exists, use `uv run <tool>`.
- Do not use `pip`, `python -m pip`, `poetry`, `pipenv`, `npm`, or `npx`.
- `app-api` and `app-worker` stay in the foreground. To run the app and get the shell back, use `make stack-up`, then `make stack-status`, `make stack-logs`, and `make stack-down`.
- `make stack-clean` deletes the database volume. Run it only when asked.
- `make db-shell` is interactive. Pass the query with `ARGS='-c "<sql>"'`.
- To convert a PDF to Markdown, follow the PDF-to-Markdown section of the runbook.

## Validation
- Code change: `make verify`.
- Change to ingestion, retrieval, answering, or the runtime containers: also run `make e2e-test`. It needs Docker.
- Docs-only change: check that the commands and links you changed exist.

## Scratch scripts
- Put temporary, exploratory, and devex scripts in `scripts/devex/`.
