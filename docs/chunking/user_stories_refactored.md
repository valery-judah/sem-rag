# User Stories: Hierarchical Segmentation for Full RAG Assistant (Rewritten)

- **Status:** Draft (v0.3)
- **Last updated:** 2026-03-02
- **Purpose:** Translate the Hierarchical Segmentation RFC into implementable user stories with testable acceptance criteria.

## Milestones (staged TDD delivery)

This document defines the **end-state** requirements. To keep implementation tractable, delivery is staged.

Each milestone introduces only the **minimum fields/concepts** necessary to (a) satisfy a downstream dependency, or (b) enforce a Phase 1 invariant (identity, anchorability, hierarchy, determinism).

### M0 -- Anchored flat passages (minimum viable segmentation)

**Deliverable**

- Emit **PASSAGE** segments from `canonical_text` with exact `[start_char_offset, end_char_offset]` and `text`.
- No hierarchy yet; no special-case splitting yet.

**Stories covered (partial where applicable)**

- US3.2 (anchorability, offsets resolve) -- partial
- US1.3 (no empty passages) -- partial
- US5.1 (structural CI gates: no empty, offsets in-bounds) -- partial

### M1 -- Deterministic ordering and position fields

**Deliverable**

- Stable ordering rules for emitted passages.
- Introduce deterministic ordinals/position fields (at least offsets; ordinals if needed for downstream assembly).

**Stories covered**

- US1.5 (ordering & offsets)

### M2 -- Deterministic IDs + golden snapshot

**Deliverable**

- Introduce deterministic `segment_id` (and config-hash if required).
- Add snapshot-based determinism test on a golden corpus.

**Stories covered**

- US3.1 (deterministic IDs)
- US1.6 (golden snapshot determinism)
- US5.1 (determinism snapshot gate) -- partial

### M3 -- Hierarchy (SECTION -> PASSAGE strict tree)

**Deliverable**

- Introduce `SECTION` nodes and `PASSAGE.parent_id` with strict-tree guarantees.
- Stable `section_path` (or equivalent) and section traversal ordering.

**Stories covered**

- US1.1 (hierarchical structure)
- US4.2 (neighbor fetch within a section) -- enables

### M4 -- Token budgets + overlap + merge-small policy

**Deliverable**

- Token counting with a deterministic tokenizer.
- Enforce `passage_tokens_min/max` with explicit merge-small and overlap behavior.

**Stories covered**

- US1.2 (token budget constraints)
- US1.4 (overlap + provenance)
- US2.5 (merge policy)
- US4.3/US4.4 (assembly and dedup contracts) -- enables

### M5 -- Special structural blocks (tables, code, lists)

**Deliverable**

- Table and code policies (atomic vs split; header repetition for table splits; logical boundaries for code).
- List/procedure integrity rules.

**Stories covered**

- US2.1-US2.4 (tables/code/lists)
- US1.2 exceptions (special segments may exceed max) -- completes

### M6 -- Full quality + eval + ops hardening

**Deliverable**

- Full intrinsic quality gates (including distribution thresholds) and quality reports in CI.
- Offline retrieval evaluation and end-to-end citation/faithfulness eval.
- Observability/metrics, churn tracking, rollout readiness.

**Stories covered**

- Epic 5 (US5.1-US5.3)
- Epic 6 (US6.1-US6.2)
- US3.3/US3.4 (churn + anchor sampling gates)

## Definitions (used across stories)

- **Segment types**
  - `SECTION`: heading-scoped node representing a document sub-tree.
  - `PASSAGE`: leaf retrieval unit intended for embedding + retrieval.
- **Hierarchy shape (v1):** a **strict tree** (each node has ≤1 parent) with **no cycles**. This satisfies the "DAG tree (no cycles)" invariant while avoiding multi-parent complexity.
- **Special passage:** a `PASSAGE` whose primary content is a **table** or **code block**; may legitimately exceed `passage_tokens_max` when preserved atomically. Must be labeled with `metadata.is_special=true` and `metadata.special_type in {"table","code"}`.
- **Position fields**
  - `metadata.passage_ordinal`: 0-based integer index of the passage within its parent section (required for PASSAGE).
  - `metadata.section_ordinal`: 0-based integer index of the section in document traversal order (required for SECTION).
  - `metadata.start_char_offset` / `metadata.end_char_offset`: offsets in `canonical_text` for deterministic ordering and debug (required for PASSAGE; optional for SECTION if anchor already implies it).
- **Tokenizer consistency:** `token_count` must be computed using a tokenizer aligned with the embedding model (or a validated proxy), deterministically.
- **Mid-sentence split:** a passage boundary that is not at a sentence boundary (excluding cases where a single sentence exceeds `passage_tokens_max`).
- **Minor edit (for churn metrics):** a document change affecting ≤5% of characters OR confined to a single paragraph/list item/table row group.

## Field & Concept Justification (why these exist)

Fields/concepts are introduced only when they unlock a downstream contract or allow tests to enforce invariants.

This table is the **schema budget**: if a field is not justified here, it should not enter the contract yet.

| Field / Concept | Why it exists (contract reason) | First milestone | Stories depending on it | Primary test(s) |
|---|---|---:|---|---|
| `start_char_offset`, `end_char_offset` | Anchorability: segment must resolve back to `canonical_text` exactly; also enables stable ordering. | M0 | US1.5, US3.2, US3.4 | Offsets in-bounds; extracted span equals `text` |
| `text` | What gets embedded/indexed; required for retrieval payloads and debug. | M0 | US4.1 | Non-empty; hash stable in snapshot |
| Deterministic ordering rule | Determinism + stable assembly; makes diffs meaningful. | M1 | US1.5, US4.3 | Ordering-by-offset (or documented tie-breakers) |
| `segment_id` | Stable identity for indexing, caching, churn tracking, and snapshot diffs. | M2 | US1.6, US3.1, US4.1, US3.3 | Determinism snapshot (normalized) |
| `SECTION` nodes | Provides hierarchy for navigation, locality, neighbor expansion, and structured context assembly. | M3 | US1.1, US4.2 | Strict-tree property tests |
| `parent_id` | Referential integrity: PASSAGE must belong to exactly one SECTION (v1 strict tree). | M3 | US1.1, US4.2 | Parent existence; no multi-parent; no cycles |
| `section_path` (or stable equivalent) | Stable hierarchy identity across runs; supports traceability and assembly. | M3 | US1.1, US3.3 | Snapshot includes path; deterministic traversal |
| `token_count` | Enforce min/max budgets and compare distributions; needed for cost/latency control. | M4 | US1.2, US4.4, US5.1 | Token bounds + histogram gates |
| `overlap_*` provenance | Prevent silent duplication; supports deterministic dedup in assembly. | M4 | US1.4, US4.3 | Overlap invariants; provenance fields present when overlap applied |
| `metadata.is_special`, `metadata.special_type` | Explicit exception mechanism: allows rule exceptions without weakening the general constraints. | M5 | US1.2, US2.* | "May exceed max only if special"; table/code tests |
| `split_reason` | Debuggability and QA: explains why boundaries occurred; helps investigate retrieval regressions. | M4 (optional) | US5.1 | Quality report includes split reasons |

## Epic 1: Core Segmentation, Hierarchy & Determinism

*Objective: Produce a stable, deterministic `SECTION -> PASSAGE` structure suitable for RAG retrieval, expansion, and citation.*

### US1.1: Build Hierarchical Structure

- **As the** hierarchical segmenter,
- **I want to** convert the parsed document structure into nested `SECTION` nodes and leaf `PASSAGE` nodes,
- **So that** downstream retrieval can fetch precise passages and expand context using section structure.

**Acceptance Criteria**

- Output is a **strict tree** with no cycles.
- Every `PASSAGE.parent_id` references an existing `SECTION.segment_id` from the same document version.
- `section_path` matches the parsed heading hierarchy (or a deterministic synthesized path for heading-less docs).
- All segments include `doc_id`, `segment_id`, `type`, and `anchor`.

### US1.2: Enforce Token Budget Constraints (with explicit exceptions)

- **As the** hierarchical segmenter,
- **I want to** enforce configurable `passage_tokens_min`, `passage_tokens_target`, and `passage_tokens_max`,
- **So that** passages are retrieval-efficient and context-window compatible.

**Acceptance Criteria**

- For **non-special** passages:
  - ≥95% have `token_count ∈ [min,max]`.
  - ≤5% may violate bounds only with an explicit `metadata.exception_reason`.
- For **special** passages (tables/code):
  - May exceed `max` if preserved atomically; must be labeled with `metadata.is_special=true` and `metadata.special_type`.
  - Must still have correct anchors and offsets.
- Token counting is deterministic and consistent across runs.

### US1.3: Boundary-Aware Splitting (measurable)

- **As the** hierarchical segmenter,
- **I want to** split at safe semantic boundaries (block/paragraph/list-item/sentence) and avoid mid-sentence cuts,
- **So that** passages remain coherent for retrieval and synthesis.

**Acceptance Criteria**

- **Empty passages never occur**.
- **Mid-sentence split rate** for non-special passages is **< 0.5%** on the golden corpus.
- Mid-sentence splits occur only when:
  - a single sentence exceeds `passage_tokens_max`, OR
  - no sentence boundary exists within the final allowable window,
  and must be labeled with `metadata.split_reason`.

### US1.4: Apply Configurable Overlap with Provenance Metadata

- **As the** hierarchical segmenter,
- **I want to** apply configurable overlap between adjacent passages aligned to safe boundaries,
- **So that** boundary queries retain context and retrieval recall improves.

**Acceptance Criteria**

- Overlap is aligned to a block or sentence boundary (never mid-token).
- Each overlapped passage includes:
  - `metadata.overlap_from_segment_id` (the previous passage id),
  - `metadata.overlap_token_count` (integer).
- Overlap is computed using the same tokenizer as `token_count`.

### US1.5: Deterministic Ordering & Position Offsets

- **As the** hierarchical segmenter,
- **I want to** emit stable ordering signals for passages and sections,
- **So that** retrieval can expand to neighbors and context builders can order/dedup deterministically.

**Acceptance Criteria**

- Every `SECTION` has `metadata.section_ordinal` (0..N-1) in document traversal order.
- Every `PASSAGE` has:
  - `metadata.passage_ordinal` within its parent section,
  - `metadata.start_char_offset` and `metadata.end_char_offset` in canonical text.
- Sorting by `(section_ordinal, passage_ordinal)` reproduces the source order deterministically.

### US1.6: Determinism (Golden Snapshot)

- **As an** operator,
- **I want** repeated runs on identical inputs to yield identical segmentation outputs,
- **So that** re-ingestion does not churn embeddings or citations unnecessarily.

**Acceptance Criteria**

- A golden snapshot test compares the full ordered segment list (IDs, anchors, ordinals, offsets, text hashes) and matches exactly across runs.
- Any intentional behavior change requires regenerating snapshots and documenting the change.

## Epic 2: Structural Block Handling (Tables, Code, Lists)

*Objective: Preserve semantics of specialized structures so retrieved passages remain interpretable and self-contained.*

### US2.1: Preserve Small Tables Atomically

- **As the** hierarchical segmenter,
- **I want to** keep tables that fit within `max_table_tokens` as atomic passages (even if exceeding `passage_tokens_max`),
- **So that** tabular relationships are preserved for reasoning.

**Acceptance Criteria**

- Tables within `max_table_tokens` are emitted as a single `PASSAGE`.
- Table passages are labeled `metadata.is_special=true`, `metadata.special_type="table"`, and include `block_types` containing `"table"`.
- Anchor and offsets cover the entire table region.

### US2.2: Split Large Tables by Row Groups with Header Repetition

- **As the** hierarchical segmenter,
- **I want to** split large tables by row groups while repeating the header row,
- **So that** each resulting passage is self-contained.

**Acceptance Criteria**

- Every split table passage contains the original header row.
- Row groups are sized to approximate `passage_tokens_target` (allowing deviation when header dominates).
- Splits never cut through a row; they occur only between rows.
- Each table-split passage is labeled as special (`special_type="table"`).

### US2.3: Split Large Code Blocks Along Logical Boundaries

- **As the** hierarchical segmenter,
- **I want to** split large code blocks along logical boundaries while preserving minimal necessary context (imports/signatures),
- **So that** code remains understandable when retrieved.

**Acceptance Criteria**

- Code ≤ `max_code_tokens` is emitted atomically and labeled `special_type="code"`.
- Code > `max_code_tokens` is split using preferred boundaries:
  1) function/class boundaries (if parser available),
  2) brace/indent blocks (language-dependent heuristics),
  3) blank-line boundaries.
- Splits never occur mid-token; if syntactic validation exists for a language, parse success rate must be tracked and regressions flagged.
- Each code passage includes language tag when available.

### US2.4: Preserve List/Procedure Integrity

- **As the** hierarchical segmenter,
- **I want to** treat list items as atomic units and preserve list intent when splitting,
- **So that** procedural steps are not orphaned.

**Acceptance Criteria**

- No list item is split unless the item alone exceeds `passage_tokens_max`.
- When lists are split across passages, each passage repeats the list header/intro sentence when available.
- List passages preserve numbering/bullets in serialization.

### US2.5: Too-Small Passage Merge Policy

- **As the** hierarchical segmenter,
- **I want to** avoid generating tiny passages by merging with neighbors when safe,
- **So that** retrieval does not return underspecified fragments.

**Acceptance Criteria**

- If a non-special passage would be `< passage_tokens_min`, the system merges it with an adjacent passage in the same section whenever this does not violate max constraints excessively.
- If merge is impossible (e.g., section boundary, special block isolation), emit the passage with `metadata.exception_reason="below_min_unmergeable"`.

## Epic 3: Identity, Anchoring & Traceability

*Objective: Stable identifiers and resolvable anchors for citations; bounded churn across versions.*

### US3.1: Deterministic Segment IDs

- **As the** segmenter,
- **I want to** generate deterministic `segment_id` values from stable inputs (doc_id, doc_version_id, section_path, anchor/span),
- **So that** identical content yields identical IDs.

**Acceptance Criteria**

- Given identical inputs (including doc_version_id), segment IDs are identical across runs.
- Segment IDs are collision-resistant (cryptographic hash or equivalent).
- Segment ID generation is covered by unit tests with fixed vectors.

### US3.2: Resolvable Source Anchors for Every Segment

- **As the** citation renderer,
- **I want** every `SECTION` and `PASSAGE` to include an `anchor_ref` that resolves to a source location,
- **So that** the UI can display precise citations.

**Acceptance Criteria**

- 100% of segments include `anchor`.
- Anchor resolution tests succeed on a sampled set per build (and on the golden corpus in CI).
- Failure modes are explicit (invalid anchor format, resolver mismatch, missing source).

### US3.3: Churn & Lineage Mapping Across Versions

- **As an** operator/data scientist,
- **I want** lineage mapping from old to new segments for changed document versions,
- **So that** I can track churn and maintain continuity in metrics and citations.

**Acceptance Criteria**

- For each doc update, system computes:
  - churn rate = `(# segments whose text-span changed materially) / (total segments)`
  - stability rate = `(# segments preserved with identical IDs) / (total segments)`
- For **minor edits**:
  - stability rate for unchanged regions is **≥ 80%**, OR lineage mapping covers **≥ 90%** of unchanged regions.
- Lineage mapping includes similarity scores and is queryable by `(doc_id, old_segment_id)`.

### US3.4: Anchor Correctness Sampling (Quality Gate)

- **As an** AI engineer,
- **I want** automated tests that validate anchors correspond to the intended segment spans,
- **So that** citation precision failures are detected early.

**Acceptance Criteria**

- Randomly sample ≥ N segments per corpus run (configurable) and validate:
  - anchor resolves to a span that overlaps `(start_char_offset, end_char_offset)` by ≥ 95%.
- Fail build on systematic mismatch above threshold.

## Epic 4: Retrieval & Context Assembly (RAG Consumer Contracts)

*Objective: Enable the RAG system to leverage hierarchy to assemble coherent, non-redundant context within a budget.*

### US4.1: Vector Indexing for Passages (and Optional Sections)

- **As a** RAG retrieval orchestrator,
- **I want to** query embeddings for `PASSAGE` (and optionally `SECTION`) items,
- **So that** I can retrieve relevant evidence efficiently.

**Acceptance Criteria**

- `PASSAGE` embeddings are indexed with `segment_id` as the primary key.
- Optional: `SECTION` embeddings are indexed with `segment_id` and `type="SECTION"` filter.
- Metadata store enables join from `segment_id -> (doc_id, section_path, anchor, ordinals, text_ref)`.

### US4.2: Neighbor Fetch / Context Expansion Within a Section

- **As a** RAG retrieval orchestrator,
- **I want to** fetch adjacent passages within the same section,
- **So that** I can expand context around a retrieved passage for coherence.

**Acceptance Criteria**

- Given a `PASSAGE.segment_id`, the system can fetch:
  - previous passage (same parent section, `passage_ordinal - 1`) if exists
  - next passage (same parent section, `passage_ordinal + 1`) if exists
- Boundary behavior is defined (first/last passage returns null for missing neighbor).
- Implementation uses either:
  - explicit `prev_id/next_id`, OR
  - indexed `(parent_id, passage_ordinal)` lookups.

### US4.3: Ordering and Overlap Deduplication for Context Assembly

- **As a** context builder,
- **I want to** order retrieved passages deterministically and deduplicate heavy overlap,
- **So that** the prompt is coherent and avoids wasted tokens.

**Acceptance Criteria**

- Ordering uses `(section_ordinal, passage_ordinal)` (and preserves within-section order).
- Dedup policy is deterministic and uses overlap provenance when available:
  - if passages share ≥ X% overlap OR one passage is mostly contained in another, keep the higher-scoring passage.
- Context builder records dedup decisions for debugging (e.g., `dropped_segment_id`, reason).

### US4.4: Context Budget Assembly Contract

- **As a** RAG system,
- **I want** an assembly contract that guarantees the final context fits a token budget while preserving evidence quality,
- **So that** generation remains stable and comparable across experiments.

**Acceptance Criteria**

- Given a target token budget B, the assembler outputs context ≤ B tokens (as measured by the same tokenizer).
- The assembler prioritizes:
  1) top-ranked passages,
  2) necessary neighbors for coherence,
  3) minimal section headers (optional),
  with deterministic tie-breaking rules.
- The assembler avoids including more than `max_passages_per_section` unless justified by ranking score thresholds (configurable).

## Epic 5: Quality Gates & Evaluation

*Objective: Quantify segmentation impact on retrieval and end-to-end RAG quality and prevent regressions.*

### US5.1: Intrinsic Quality Gates (CI)

- **As an** AI engineer,
- **I want** fast assertions to run on every build,
- **So that** segmentation regressions are blocked before embedding.

This story is intentionally staged:

#### US5.1a -- Structural CI gates (M0-M3)

**Purpose:** catch "must-never-happen" failures early.

**Acceptance Criteria**

- Fail build on the golden corpus if any occur:
  - any empty PASSAGE (`text.strip()==""`)
  - offsets out of bounds (`0 <= start < end <= len(canonical_text)`)
  - missing required fields for the current milestone's contract
  - strict-tree violation once hierarchy exists (M3): cycles, orphan PASSAGE, multiple parents
  - determinism snapshot mismatch once IDs exist (M2+)

#### US5.1b -- Distribution / policy gates (M4+)

**Purpose:** enforce quality and policy thresholds after the mechanics are stable.

**Acceptance Criteria (default thresholds; configurable)**

- Fail build on the golden corpus if any occur:
  - mid-sentence split rate ≥ 0.5% (non-special)
  - table-split passages missing repeated header row (when table splitting is enabled)
  - token budget violations outside explicit exceptions (special segments only)
- Emit a quality report artifact with counts and histograms (token distribution, split reasons, special counts, anomaly counts).

### US5.2: Offline Retrieval Evaluation (IR Eval)

- **As an** AI engineer,
- **I want** offline IR evaluation (Recall@k, MRR@k, nDCG@k, evidence coverage),
- **So that** improvements are objective and reproducible.

**Acceptance Criteria**

- Metrics are computed on a labeled dataset of `(query, relevant_span)` pairs.
- New segmenter shows **no regression** vs baseline on Recall@k, and improvements are tracked.
- Evidence coverage is reported (fraction of required facts present in retrieved set).

### US5.3: End-to-End Faithfulness & Citation Evaluation

- **As an** AI engineer,
- **I want** end-to-end evaluation of answer correctness, faithfulness, and citation precision,
- **So that** segmentation improves final assistant quality.

**Acceptance Criteria**

- Unsupported-claim rate decreases vs baseline (threshold TBD per domain).
- Citation precision improves vs baseline (threshold TBD per domain).
- A random subset receives human audit to calibrate automated judges.

## Epic 6: Observability & Operations

*Objective: Ensure the system is debuggable and measurable in production and during experiments.*

### US6.1: Emit Segmentation Events and Metrics

- **As an** operator,
- **I want** structured events and metrics from the segmenter,
- **So that** I can diagnose failures and correlate with retrieval/answer regressions.

**Acceptance Criteria**

- Emit `DocSegmented(doc_id, sections, passages)` plus counters:
  - token_count histogram (p50/p90/p99)
  - special passage counts (table/code)
  - mid-sentence split rate
  - below-min merge count
  - churn/stability metrics on updates (when applicable)
- Metrics are keyed by `doc_id`, source type, and segmenter version.

### US6.2: Segmenter Versioning and Reproducibility

- **As an** operator,
- **I want** segmenter versioning and config capture,
- **So that** outputs can be reproduced exactly for audits and rollbacks.

**Acceptance Criteria**

- Every run records:
  - segmenter version,
  - config hash,
  - tokenizer version,
  - doc_version_id.
- These are attached to published artifacts or metadata store entries.

## Appendix: Suggested Defaults (initial)

- `passage_tokens_min`: 300
- `passage_tokens_target`: 600
- `passage_tokens_max`: 900
- `overlap_ratio`: 0.10
- `mid_sentence_split_rate` gate: < 0.5% (non-special)
- Minor edit definition: ≤5% char change or single paragraph/list item/table row group
