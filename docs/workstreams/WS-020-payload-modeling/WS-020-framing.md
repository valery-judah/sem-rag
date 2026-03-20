# Framing

## Problem
The `interpret` and `retrieve` stages serialize their trace payloads as raw inline dictionaries rather than structured Pydantic models. This breaks the repository's "Structured domain models" rule and forces downstream consumers like `QueryReplayService` to parse raw `dict[str, Any]` data, requiring `# pyright: ignore` pragmas to silence static type checking errors at the boundary.

## Scope
- Introducing `InterpretationTracePayload` and `RetrievalTracePayload` models to `src/doc_forge/query/stages/interpret.py` and `src/doc_forge/query/stages/retrieve.py`.
- Updating `src/doc_forge/query/replay.py` to deserialize these models instead of performing manual dynamic `list` comprehensions.
- Removing the associated `# pyright: ignore` workarounds from `replay.py`.

## Constraints
- The fix must align with `docs/engineering/python-domain-modeling.md`, specifically "Use Pydantic `BaseModel` for structured domain data" and "Validate at boundaries".
- `model_config = ConfigDict(extra="forbid")` must be set on the payload models.
- The JSON payload schema output by the stages must remain structurally identical to maintain backwards compatibility with already persisted traces.

## Input context
- paths: `src/doc_forge/query/stages/interpret.py`, `src/doc_forge/query/stages/retrieve.py`, `src/doc_forge/query/replay.py`
- read first: `docs/engineering/python-domain-modeling.md`

## Key decisions
- **Payload Schema Guarantee:** The payload models must map 1:1 to the current inline dictionary structures (e.g., matching the exact 8 fields generated in `retrieve.py`).

## Expected outputs
- Pydantic models for Stage 2 and Stage 3 trace payloads.
- Clean `uv run poe type` output without requiring `# pyright: ignore` pragmas for trace payload deserialization in `replay.py`.

## Exit criteria
- The trace payloads are fully modeled in Pydantic.
- `replay.py` uses `.model_validate()` and accesses strongly typed objects downstream.
- Code mode execution completes safely and successfully passes strict Pyright checks without pragmas on those lines.

## Objective
Implement Pydantic models for Stage 2 (Interpret) and Stage 3 (Retrieve) query trace payloads to enforce boundary validation and eliminate `# pyright: ignore` pragmas from replay logic.

## Non-goals
- Redesigning the query pipeline or tracing format.
- Modifying the core `Interpreter` or `Retriever` domain logic (`QueryInterpretationResult` or `QueryRetrievalResult`).
- Altering other existing stage payloads (e.g., `SelectionTracePayload`).

## Relevant context
- Stage 4 (`select.py`) uses `SelectionTracePayload(BaseModel)` to enforce structure before assigning to `QueryStageTrace.payload`.
- Stages 2 and 3 currently define their `payload=` as an inline `dict`.
- The `replay.py` consumer reconstructs these objects by extracting raw dictionary values, which defeats the type checker.
- paths: `src/doc_forge/query/replay.py`, `src/doc_forge/query/stages/retrieve.py`, `src/doc_forge/query/stages/interpret.py`
- components: `QueryReplayService`, `run_interpret_stage`, `run_retrieve_stage`
- constraints: Maintain identical serialized JSON footprint for backwards compatibility with legacy traces.

## Workflow steps
1. **Model Definition**: Create `InterpretationTracePayload` matching `{"interpreted_query": ..., "interpreter": ...}` and `RetrievalTracePayload` matching the existing 8 fields in `retrieve.py`.
2. **Runner Refactor**: Update the `run()` functions in those modules to instantiate the models and pass `payload.model_dump(mode="json")` into `QueryStageTrace`.
3. **Replay Refactor**: Update `_reconstruct_retrieved_candidates` and `_reconstruct_interpreted_query` in `replay.py` to use `.model_validate()`.
4. **Validation**: Run type checks and ensure no pragmas are needed for these specific fields.

## Validation and Definition of Done
- [x] `uv run poe type` reports no errors in `src/doc_forge/query/`.
- [x] No new or unexpected errors arise in test suites (`uv run poe verify`).
- [x] Backwards compatibility is preserved (field names and types haven't changed).

## Linked artifacts
- `docs/engineering/python-domain-modeling.md`
