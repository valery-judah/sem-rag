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

Default behavior remains lightweight and deterministic. Model-backed paths are opt-in through environment configuration.

## Runtime wiring
[`src/parity/app/settings.py`](../../../src/parity/app/settings.py) exposes the relevant process configuration:

- `PARITY_EMBEDDING_BACKEND`
- `PARITY_EMBEDDING_MODEL`
- `PARITY_ANSWER_GENERATOR_BACKEND`
- `PARITY_ANSWER_GENERATOR_MODEL`
- `PARITY_ANSWER_GENERATOR_MAX_NEW_TOKENS`
- `PARITY_ANSWER_GENERATOR_TEMPERATURE`

[`src/parity/app/deps.py`](../../../src/parity/app/deps.py) resolves those settings into concrete runtime adapters:

- embedding backends
  - `DeterministicEmbeddingAdapter`
  - `SentenceTransformerEmbeddingAdapter`
- answer generators
  - `DeterministicGroundedAnswerGenerator`
  - `MlxGroundedAnswerGenerator`
  - `OllamaGroundedAnswerGenerator`

If an unsupported backend string is provided, dependency wiring fails fast with an explicit runtime error.

## Optional dependency model
[`pyproject.toml`](../../../pyproject.toml) keeps the optional ML stack separated from the default install:

- `llm`
  - `sentence-transformers`
  - `torch`
- `mac`
  - `mlx-lm`

This keeps the default contributor workflow small while still allowing real local retrieval and local generation experiments.

## Embedding path
[`src/parity/indexing/embeddings.py`](../../../src/parity/indexing/embeddings.py) keeps deterministic embeddings as the default indexing path and adds an opt-in `SentenceTransformerEmbeddingAdapter`.

Important behavior:

- `require_sentence_transformers()` gives an explicit setup error when the optional `llm` group is missing
- the default embedding model is `sentence-transformers/all-MiniLM-L6-v2`
- the real embedding path is used by both indexing and dense retrieval when `PARITY_EMBEDDING_BACKEND=sentence-transformers`

## Answer-generation path
[`src/parity/query/answer_generation.py`](../../../src/parity/query/answer_generation.py) now contains:

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

For the Docker-backed smoke workflow, the repo now prefers host-native Ollama on Apple Silicon instead of the Docker `ollama` container. [`run_and_query.sh`](../../../run_and_query.sh) defaults `USE_HOST_OLLAMA=1` on `Darwin arm64`, points containers at `http://host.docker.internal:11434`, and starts `ollama serve` on the host when needed.

That change was made because the practical fast path on macOS is host Ollama using Metal acceleration rather than CPU-bound container inference.

## Multi-document comparison smoke harness
[`run_and_query.sh`](../../../run_and_query.sh) is no longer a single-document smoke test. It now acts as a comparison harness for the current local-LLM path.

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

- `tinyllama` often collapses to the deterministic fallback rather than producing a materially different answer
- the current smoke script checks structural comparison properties, not semantic answer quality
- answer quality for small local models remains a product problem, not just an infrastructure problem

## Validation references
Relevant tests for this work include:

- [`tests/indexing/test_model_embeddings.py`](../../../tests/indexing/test_model_embeddings.py)
- [`tests/query/test_query_llm_generation.py`](../../../tests/query/test_query_llm_generation.py)
- [`tests/query/test_query_answer_generation.py`](../../../tests/query/test_query_answer_generation.py)
- [`tests/app/test_optional_backends.py`](../../../tests/app/test_optional_backends.py)

Useful local commands:

- `make sync-llm`
- `make sync-mac`
- `make smoke-llm`
- `make smoke-mac`
- `./run_and_query.sh`

## Scope notes
- This workstream does not introduce a stable public API.
- Backend selection remains an internal runtime seam.
- The canonical product and architecture docs should only be updated when this optional local-LLM path becomes durable project truth rather than workstream-local implementation detail.
