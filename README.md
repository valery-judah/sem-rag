# docforge

Python-based semantic RAG baseline project.

## What is included
- `src/docforge/`: small semantic retrieval library and CLI demo
- `tests/`: unit tests for retrieval behavior
- `Makefile`: standardized `uv`-based workflow
- `AGENTS.md`: repository agent/development rules

## Quickstart
```bash
make sync
make install
make test
make run
```

## Secret scanning

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

## Repository layout
```text
src/docforge/
  __init__.py
  cli.py
  retrieval.py
tests/
  test_retrieval.py
```
