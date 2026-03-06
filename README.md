# docforge

Semantic-pipeline MVP for turning raw internal documents into structured, queryable knowledge artifacts.

The repo currently spans source connectors, canonical parsing, PDF-hybrid extraction, segmentation, a lightweight retrieval demo, and feature-level implementation docs.

## Read First

- `AGENTS.md`: agent and workflow entry point
- `ARCHITECTURE.md`: current repo/module map
- `docs/README.md`: documentation index
- `docs/mvp-1.md`: MVP semantic-pipeline north star

These docs form the control plane for the repository. Feature-specific contracts stay in `docs/features/*/01_rfc.md`.

## What Is In This Repo

- `src/docforge/connectors/`: source-document contracts and connector implementations
- `src/docforge/parsers/`: canonical parsing, structure extraction, and PDF-hybrid parsing work
- `src/docforge/segmentation.py`: segmentation logic for parser output
- `src/docforge/retrieval.py` and `src/docforge/cli.py`: lightweight retrieval demo surface
- `docs/features/`: feature-level RFCs, designs, and workplans
- `tests/`: unit coverage for connectors, parsers, retrieval, and PDF-hybrid components

## Quickstart

```bash
make sync
make install
make test
make run
```

## Secret Scanning

This repo includes a local Gemini API key scan for strings that match the format-aware
`AIza[A-Za-z0-9_-]{35}` pattern. Version 1 scans only Gemini-style keys, has no allowlist, and
keeps CI `gitleaks` checks as separate defense in depth.

Run a repo-wide audit of tracked files:

```bash
make secret-scan
```

Install the repo-managed pre-commit hook:

```bash
make install-git-hooks
```

After installation, each commit scans staged added lines only. It does not scan unchanged old
lines, full git history, or non-staged working tree changes.

## Repository Map

```text
AGENTS.md
ARCHITECTURE.md
docs/
  README.md
  mvp-1.md
  PIPELINE.md
  PLANS.md
  features/
src/docforge/
tests/
```
