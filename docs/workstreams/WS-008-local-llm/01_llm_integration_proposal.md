# WS-008: Local LLM Integration Implementation Note

## Overview
This workstream now reflects the implemented repo state for optional real embeddings and optional Apple Silicon local answer generation.

The implementation intentionally adopts only the runtime-relevant subset of the `simple-local-rag` Mac stack. `parity` does not carry over notebook or tutorial dependencies such as `jupyter`, `matplotlib`, `pandas`, `spacy`, `tqdm`, or parsing alternatives such as `PyMuPDF`. The repository continues to use `pypdf` for document parsing and [`uv.lock`](../../../uv.lock) as the only lock source.

## Implemented Changes

### 1. Dependency split in `uv`
The dependency model is now split across optional groups in [`pyproject.toml`](../../../pyproject.toml):

- `llm`
  - `sentence-transformers`
  - `torch`
- `mac`
  - `mlx-lm`

This replaces the earlier idea of maintaining a standalone `requirements-mac.txt` inside `parity`.

### 2. Optional embedding backend
[`src/parity/indexing/embeddings.py`](../../../src/parity/indexing/embeddings.py) now includes:

- `DeterministicEmbeddingAdapter` as the default lightweight path
- `SentenceTransformerEmbeddingAdapter` as the optional real embedding path
- `require_sentence_transformers()` for explicit smoke/failure messaging when the `llm` group is not installed

The runtime wiring in [`src/parity/app/deps.py`](../../../src/parity/app/deps.py) keeps deterministic embeddings as the default and only activates the model-backed path when configured.

### 3. Optional Apple Silicon answer generation
[`src/parity/query/answer_generation.py`](../../../src/parity/query/answer_generation.py) now includes:

- `DeterministicGroundedAnswerGenerator` as the default Stage 7 path
- `MlxGroundedAnswerGenerator` as the optional Apple Silicon local generation path
- `require_mlx_lm()` for explicit smoke/failure messaging when the `mac` group is not installed

The MLX generator:

- builds a grounded prompt from the current `ContextManifest`, `SupportAssessment`, and `AnswerModeDecision`
- uses lazy imports so the base repo install does not depend on `mlx-lm`
- falls back to the deterministic path for full abstention and as the default runtime behavior unless explicitly configured

### 4. Runtime selection
[`src/parity/app/settings.py`](../../../src/parity/app/settings.py) and [`src/parity/app/deps.py`](../../../src/parity/app/deps.py) now support explicit backend selection via environment variables:

- `PARITY_EMBEDDING_BACKEND`
  - supported values: `deterministic`, `sentence-transformers`
- `PARITY_EMBEDDING_MODEL`
- `PARITY_ANSWER_GENERATOR_BACKEND`
  - supported values: `deterministic`, `mlx`
- `PARITY_ANSWER_GENERATOR_MODEL`
- `PARITY_ANSWER_GENERATOR_MAX_NEW_TOKENS`
- `PARITY_ANSWER_GENERATOR_TEMPERATURE`

Default behavior remains deterministic for both embeddings and answer generation, which preserves the existing lightweight local workflow and current tests.

### 5. Makefile support
[`Makefile`](../../../Makefile) now exposes optional install and smoke targets:

- `make sync-llm`
- `make sync-mac`
- `make smoke-llm`
- `make smoke-mac`

These are additive. Existing `make sync`, `make install`, `make test`, and `make verify` behavior remains unchanged for contributors who do not need the optional ML stack.

## Validation
The implementation was validated with the following results:

- `make test`
  - passed
- focused Ruff checks on changed files
  - passed
- focused tests for optional backends
  - passed
- `make smoke-llm` without the optional group installed
  - failed with the intended guidance message telling the user to run `make sync-llm` or `uv sync --group llm`

Focused tests added for this work include:

- [`tests/indexing/test_model_embeddings.py`](../../../tests/indexing/test_model_embeddings.py)
- [`tests/query/test_query_llm_generation.py`](../../../tests/query/test_query_llm_generation.py)
- [`tests/app/test_optional_backends.py`](../../../tests/app/test_optional_backends.py)

## Notes
- This workstream does not promote any stable public API. The backend selection and Stage 7 generation seams remain internal implementation details.
- The current repo still defaults to deterministic embeddings and deterministic generation. The optional ML paths are opt-in and intended for local experimentation and future expansion.
