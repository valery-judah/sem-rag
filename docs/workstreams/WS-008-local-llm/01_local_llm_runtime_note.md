# WS-008: Local LLM Runtime Note

## Purpose
This note records the current local-LLM runtime shape that actually exists in the repo. It replaces the earlier proposal framing with implementation truth for optional model-backed embeddings, optional local answer generation, and the end-to-end smoke path used to compare deterministic and LLM-backed answers.

This is a workstream note, not a canonical product contract. Durable runtime truth still belongs in the evergreen docs.

## Current repo state
The repo now supports three answer-generation paths and two embedding paths:

- embeddings
  - `deterministic`
  - `sentence-transformers`
- answer generation
  - `deterministic`
  - `mlx`
  - `ollama`

Default process behavior remains lightweight and deterministic. Docker-backed
local workflows on Apple Silicon now auto-select host Ollama when it is
reachable; other hosts and non-Docker process entrypoints stay deterministic
unless explicitly configured.

## Runtime wiring
[`src/doc_forge/app/settings.py`](src/doc_forge/app/settings.py) exposes the relevant process configuration:

- `DOC_FORGE_EMBEDDING_BACKEND`
- `DOC_FORGE_EMBEDDING_MODEL`
- `DOC_FORGE_ANSWER_GENERATOR_BACKEND`
- `DOC_FORGE_ANSWER_GENERATOR_MODEL`
- `DOC_FORGE_ANSWER_GENERATOR_MAX_NEW_TOKENS`
- `DOC_FORGE_ANSWER_GENERATOR_TEMPERATURE`

[`src/doc_forge/app/deps.py`](src/doc_forge/app/deps.py) resolves those settings into concrete runtime adapters:

- embedding backends
  - `DeterministicEmbeddingAdapter`
  - `SentenceTransformerEmbeddingAdapter`
- answer generators
  - `DeterministicGroundedAnswerGenerator`
  - `MlxGroundedAnswerGenerator`
  - `OllamaGroundedAnswerGenerator`

If an unsupported backend string is provided, dependency wiring fails fast with an explicit runtime error.

## Optional dependency model
[`pyproject.toml`](pyproject.toml) keeps the optional ML stack separated from the default install:

- `llm`
  - `sentence-transformers`
  - `torch`
- `mac`
  - `mlx-lm`

This keeps the default contributor workflow small while still allowing real local retrieval and local generation experiments.

## Embedding path
[`src/doc_forge/indexing/embeddings.py`](src/doc_forge/indexing/embeddings.py) keeps deterministic embeddings as the default indexing path and adds an opt-in `SentenceTransformerEmbeddingAdapter`.

Important behavior:

- `require_sentence_transformers()` gives an explicit setup error when the optional `llm` group is missing
- the default embedding model is `sentence-transformers/all-MiniLM-L6-v2`
- the real embedding path is used by both indexing and dense retrieval when `DOC_FORGE_EMBEDDING_BACKEND=sentence-transformers`

## Answer-generation path
[`src/doc_forge/query/answer_generation.py`](src/doc_forge/query/answer_generation.py) now contains:

- the deterministic Stage 7 renderer
- the MLX-backed local generator
- the Ollama-backed local generator

The current Stage 7 behavior is:

- deterministic generation is still the baseline path
- both `mlx` and `ollama` build grounded prompts from the interpreted query, support assessment, answer mode, and assembled context
- full abstention still falls back to the deterministic path
- prompt-echo or malformed LLM output is normalized or replaced with the deterministic fallback
- comparison questions now render a deterministic comparison fallback that mentions both sides when the evidence supports that shape

## Apple Silicon and GPU-backed local generation
Two local generation options now exist on macOS:

- `mlx`
  - pure in-process Apple Silicon path via `mlx-lm`
- `ollama`
  - local HTTP generation path via Ollama

For Docker-backed local operation, the repo now prefers host-native Ollama on
Apple Silicon instead of the Docker `ollama` container.

Current behavior:

- `make docker-up-build`
- `make test-e2e`
- [`scripts/compare_answer_backends.sh`](../../scripts/compare_answer_backends.sh)

all default to host Ollama on `Darwin arm64` when it is reachable, point
containers at `http://host.docker.internal:11434`, and use `llama3.2:1b`
unless explicitly overridden.

That change was made because the practical fast path on macOS is host Ollama using Metal acceleration rather than CPU-bound container inference.

The Compose `ollama` service still exists, but it is now behind an opt-in
profile for explicit fallback/debug use rather than part of the default local
stack.

## Multi-document comparison smoke harness
[`scripts/compare_answer_backends.sh`](../../scripts/compare_answer_backends.sh) is no longer a single-document smoke test. It now acts as a comparison harness for the current local-LLM path.

The script:

- creates a temp workspace and synthetic markdown corpus
- uploads three docs into one workspace
  - `Atlas Cache Design`
  - `Beacon Dashboard Cache`
  - `Comet Background Notes`
- waits for all docs to reach `ready`
- keeps embeddings fixed at `sentence-transformers`
- runs the same comparison question twice
  - first with `deterministic`
  - then with `ollama`
- recreates only the `api` service when switching answer generators
- verifies embedding proof from worker logs
- verifies Ollama generation proof from API logs
- prints a side-by-side comparison report with:
  - `query_id`
  - `support_state`
  - `answer_mode`
  - `generator_version`
  - cited material docs
  - answer text
  - simple comparison booleans

The script also uses a unique workspace per run so repeated executions do not contaminate retrieval with old uploads.

## What the smoke run proves today
The current smoke path proves infrastructure more strongly than answer quality.

What is working:

- model-backed embeddings are exercised during ingestion
- the Ollama generator is exercised during query answering
- Apple Silicon host Ollama can run the second query on GPU
- the comparison query cites Atlas and Beacon rather than the unrelated Comet doc
- deterministic and LLM-backed runs both return `support_state=sufficient`

What remains limited:

- very small local models can still collapse to deterministic fallback behavior rather than producing a materially different answer
- the current smoke script checks structural comparison properties, not semantic answer quality
- answer quality for small local models remains a product problem, not just an infrastructure problem

## Validation references
Relevant tests for this work include:

- [`tests/indexing/test_model_embeddings.py`](tests/indexing/test_model_embeddings.py)
- [`tests/query/test_query_llm_generation.py`](tests/query/test_query_llm_generation.py)
- [`tests/query/test_query_answer_generation.py`](tests/query/test_query_answer_generation.py)
- [`tests/app/test_optional_backends.py`](tests/app/test_optional_backends.py)

Useful local commands:

- `make sync-llm`
- `make sync-mac`
- `make smoke-llm`
- `make smoke-mac`
- `./scripts/compare_answer_backends.sh`

## Scope notes
- This workstream does not introduce a stable public API.
- Backend selection remains an internal runtime seam.
- The canonical product and architecture docs should only be updated when this optional local-LLM path becomes durable project truth rather than workstream-local implementation detail.
