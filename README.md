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

## Repository layout
```text
src/docforge/
  __init__.py
  cli.py
  retrieval.py
tests/
  test_retrieval.py
```
