# WS-008: Local LLM Integration Proposal

## Overview
This proposal outlines the strategy for introducing local LLM generation into the `parity` repository. Based on an analysis of the `simple-local-rag` project and the current architecture of `parity`, we will implement a new Local LLM generator that replaces or supplements the deterministic answer generation in Stage 7 of the query pipeline.

## Architectural Changes

### 1. Stage 7 Generation Enhancements
The current implementation relies on [`DeterministicGroundedAnswerGenerator`](src/parity/query/answer_generation.py:53) in [`src/parity/query/answer_generation.py`](src/parity/query/answer_generation.py). 

We will introduce a new `LlmGroundedAnswerGenerator` that conforms to the [`GroundedAnswerGenerator`](src/parity/query/answer_generation.py:36) protocol. This new class will:
- Consume the `ContextManifest`, `SupportAssessment`, and `AnswerModeDecision`.
- Construct a prompt incorporating the grounded evidence sets and the requested `answer_mode`.
- Use an integrated LLM to generate the final text instead of deterministically joining snippets.

### 2. Dependency Management & Apple Silicon Support
Following the `simple-local-rag` precedent, we need to handle multi-platform dependencies, specifically to support Apple Silicon via the `mlx-lm` library.
Since our project relies strictly on `uv` and `pyproject.toml`, we propose the following changes:
- Define a macOS-specific dependency group in [`pyproject.toml`](pyproject.toml) (e.g., `mac` group containing `mlx-lm`), or utilize a separate requirements file like `requirements-mac.txt` if native `uv` groups are insufficient.
- Maintain `uv.lock` as the single source of truth, updating it after dependency changes.

### 3. Build & Makefile Updates
We will enhance the existing [`Makefile`](Makefile) to mirror the caching and target isolation found in `simple-local-rag`:
- **Model Caching:** Expose environment variables such as `HF_HOME` and `HUGGINGFACE_HUB_CACHE` to avoid redownloading models.
- **Platform-specific Targets:**
  - Add `sync-mac` / `install-mac` targets to handle the `mlx-lm` dependency installation.
  - Add `smoke` and `smoke-mac` targets. The `smoke-mac` target will execute integration tests specifically exercising the `LlmGroundedAnswerGenerator` on Apple Silicon hardware.

## Implementation Steps

1. **Update Dependencies:**
   - Add `mlx-lm` to a `mac` dependency group in [`pyproject.toml`](pyproject.toml).
   - Run `uv sync` (or `uv sync --group mac`) to update `uv.lock`.

2. **Update Makefile:**
   - Add `HF_HOME` and `HUGGINGFACE_HUB_CACHE` export caching.
   - Introduce `make sync-mac` and `make smoke-mac`.

3. **Implement Generator:**
   - Create `LlmGroundedAnswerGenerator` in [`src/parity/query/answer_generation.py`](src/parity/query/answer_generation.py) (or a dedicated module).
   - Implement the prompt formatting and local model execution via `mlx-lm`.

4. **Testing & Validation:**
   - Create tests to validate the correct generation logic within the boundaries of the [`GroundedAnswerGenerator`](src/parity/query/answer_generation.py:36) contract.
   - Add a lightweight smoke test for the `smoke-mac` target.
