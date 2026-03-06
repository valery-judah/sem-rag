# Local Development Runbook

**Status:** Scaffold

This file is reserved for the future local runtime story of the semantic pipeline once the repo grows beyond the current single-environment MVP.

## Current State

Today the repo does not define:

- `docker-compose.yml`
- database bring-up or reset commands
- migration workflows
- local multi-service observability stack

Current development uses the repo-local Python workflow documented in:

- [`../../AGENTS.md`](../../AGENTS.md)
- [`../../README.md`](../../README.md)

## What Will Live Here Later

When local runtime orchestration exists, this runbook should document:

- how to boot the local stack
- how to stop and reset local state
- how to seed sample data or corpora
- how to inspect service logs and artifacts
- how to run smoke checks against the composed environment

## Guardrail

Do not add hypothetical commands here before the runtime surface exists. This runbook should stay explicitly scaffolded until `docker-compose` or an equivalent local orchestration path lands in the repo.
