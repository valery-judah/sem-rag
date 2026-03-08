# Runbook

## Purpose
This file captures durable operational guidance for working in this repository. Use it for common local commands, troubleshooting, and ownership notes.

## When To Use
- Bootstrapping the repo locally
- Running the standard validation loop
- Looking for the first place to document an operational issue

## Local Setup / Common Commands
```bash
make sync
make install
make test
make run
```

Additional checks:
```bash
make fmt
make lint
make type
make secret-scan
```

## Deploy / Release Notes
- This repo currently centers on local development and demo execution.
- Record any future release or deployment process changes here once they become stable.
- Keep temporary rollout notes inside the relevant workstream until they are durable.

## Troubleshooting
- If imports fail, run `make sync` and `make install`.
- If validation disagrees across environments, re-run the standard `fmt`, `lint`, `type`, and `test` targets.
- If parser behavior changes unexpectedly, check the relevant workstream docs in `docs/workstreams/` and recent workstream evidence.

## Escalation / Ownership
- Architectural decisions that affect multiple subsystems should be captured in `docs/adrs/`.
- Time-scoped investigation, implementation notes, and handoff material should live under `docs/workstreams/`.
- Repo-specific conventions and templates live under `docs/harness/`.
