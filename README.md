# doc_forge

doc_forge answers questions over a bounded corpus of uploaded PDF and Markdown files and shows the
evidence behind each answer. The product scope is in [`docs/evergreen/mvp.md`](docs/evergreen/mvp.md),
and [`docs/evergreen/architecture.md`](docs/evergreen/architecture.md) says how much of it is built.

## Requirements
- Python 3.11+ and [`uv`](https://docs.astral.sh/uv/)
- Docker with Compose, for the local stack and the end-to-end tests
- Optional: [Ollama](https://ollama.com/) with `llama3.2:1b` for generated answers on Apple
  Silicon

## Quick start

```bash
make setup
make verify
```

Start Postgres, the API, and the worker in Docker:

```bash
make stack-up
```

The API is on `http://127.0.0.1:8000`. Check the stack with `make stack-status` and
`make stack-logs`, and stop it with `make stack-down`.

To work on the API or the worker with reload, stop the stack, start only its Postgres, and run
them on the host, each in its own terminal:

```bash
make stack-up-db
make db-migrate
make app-api
make app-worker
```

Run the end-to-end tests. They build an image and start their own containers, so they don't need
the stack:

```bash
make e2e-test
```

`make help` lists every command. The [runbook](docs/evergreen/runbook.md) explains when to use
each one.

## Optional dependencies
- `make setup-llm` installs sentence-transformers for model-backed embeddings.
- `make setup-mac` also installs MLX for answer generation on Apple Silicon.

`make setup-sync` removes these groups again, so rerun the one you need after it.

## PDF-to-Markdown conversion
Agents can convert a PDF into a Markdown copy with Marker and a local OCR model. Ask with an
absolute path, for example "Convert /absolute/path/to/source.pdf to Markdown." The conversion
runs locally and is separate from the `pypdf` ingestion that the app uses. The
[runbook](docs/evergreen/runbook.md#pdf-to-markdown-conversion) has the steps, the command, and
the checks.

## Docs
- [Docs index](docs/README.md)
- [Runbook](docs/evergreen/runbook.md): commands, local workflows, and troubleshooting
- [Observability operations](docs/evergreen/observability-operations.md): logs, query bundles,
  and the observability stack
- [MVP](docs/evergreen/mvp.md), [architecture](docs/evergreen/architecture.md), and
  [API contracts](docs/evergreen/api-contracts.md)

## Configuration
- Runtime settings come from `.env`. See `.env.example` and the runbook's configuration
  section.
- Host `uv` commands use the repository-local cache in `./.tmp_uv_cache`, set in `uv.toml`.
- Packaging and tools: `pyproject.toml`. Python tasks: `poe_tasks.toml`.

Added Keys (test anti-clone)
