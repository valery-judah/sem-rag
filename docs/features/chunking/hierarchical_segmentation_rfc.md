# RFC: Hierarchical Segmentation for Full RAG Assistant

- **Status:** Draft (v0.1)
- **Owner:** (TBD)
- **Reviewers:** (TBD)
- **Last updated:** 2026-03-02
- **Related:** Phase 1 Knowledge Representation Pipeline (Segmenter component + downstream embedding/indexing/publishing)

## 1. Summary

This RFC specifies a **hierarchical segmentation** capability that converts a parsed document into stable, anchorable, nested retrieval units:

- `DOCUMENT -> SECTION -> PASSAGE`

The primary consumer is a **full RAG assistant**. Segmentation must improve retrieval and synthesis quality by producing passages that are (1) semantically coherent, (2) structurally aligned to the source, (3) sized appropriately for embedding + context assembly, and (4) **traceable via stable IDs and anchors**.

This document defines:

- scope and success criteria
- segment schema and invariants
- anchoring and identity rules
- segmentation policy + edge-case handling (tables, code, lists)
- retrieval/context assembly integration assumptions
- quality definition (NLP/IR rationale + measurable metrics)
- test plan, observability, rollout, and open decisions

## 2. Motivation
### 2.1 Why hierarchy (vs flat chunking)

A flat chunking strategy is insufficient for a full RAG assistant because it cannot reliably support:

- **Section-aware expansion** (retrieve a small passage, then expand to neighbors/parent section for coherence)
- **Stable citation** (anchors and IDs that map to a specific part of the source)
- **Incremental updates with bounded churn** (small edits should not reshuffle all chunk IDs)
- **Structure preservation** (tables/code/numbered procedures should not be shredded)

### 2.2 NLP/IR rationale for segmentation quality

Segmentation quality directly impacts RAG outcomes due to:

- **Vector dilution (topical mixing):** Embeddings represent aggregate semantics. If a passage mixes unrelated topics (e.g., configuration + troubleshooting + API spec), nearest-neighbor retrieval precision decreases.
- **Boundary misalignment:** Splitting across discourse units (definitions, step lists, table headers) produces incomplete evidence. The generator then "fills gaps" (faithfulness risk) or produces incoherent explanations.
- **Coreference and entity resolution:** Overly small passages break antecedents ("it", "this", "the service"), harming both retrieval and synthesis.
- **Budget efficiency:** Overly large passages waste context budget, increase truncation risk, and can bury the relevant sentence inside irrelevant tokens.

This RFC therefore defines both **intrinsic** (segment-level) quality gates and **extrinsic** (retrieval + end-to-end) evaluation.

## 3. Goals and Non-Goals
### 3.1 Goals (v1)

1. **Deterministic segmentation**: same parsed inputs ⇒ identical segments and IDs.
2. **Stable identity + traceability**:
   - segment IDs stable within a doc version;
   - when content changes, segments may change but should remain traceable with bounded churn.
3. **Anchorability**: every segment has an anchor that resolves back to the source.
4. **Hierarchical integrity**: parent-child relationships form an acyclic tree (or DAG tree if needed), no cycles.
5. **RAG-quality improvements**:
   - higher retrieval precision/recall vs baseline flat chunking;
   - improved citation accuracy and answer faithfulness on offline eval.
6. **Structure-aware handling**:
   - tables and code blocks preserved and segmented without destroying semantics.

### 3.2 Non-Goals (v1)

- LLM-based segmentation decisions as the default (may be explored later for specialized corpora).
- Cross-document topic modeling or global clustering.
- Personalized segmentation by user or org.
- Runtime orchestration, caching/latency, or full A/B infra mechanics (tracked separately).

## 4. Scope and System Context
### 4.1 Pipeline placement

This segmenter consumes the outputs of a Structural Parser/Distiller:

- `canonical_text`
- `structure_tree` with headings/lists/tables/code blocks
- anchors for document/sections/blocks (including offset ranges)

It produces a list of `SECTION` and `PASSAGE` segments which are later embedded, indexed, and published to stores (vector + metadata; lexical optional).

### 4.2 Consumers

- **Embedding + Vector index**: embed `PASSAGE` segments (required); optionally `SECTION` (useful for hierarchical retrieval).
- **RAG Retrieval Orchestrator**:
  - fetch top-k passages (and optionally sections/views),
  - rerank,
  - expand context (neighbors/parent section) under token budget.
- **Context Builder**: order segments, deduplicate overlaps, stitch into coherent context blocks.
- **Citation Renderer**: resolve `anchor_ref` back to the source location.

## 5. Terminology

- **Document**: a source artifact with stable `doc_id`.
- **Section**: a heading-scoped subtree in the structure tree; contains blocks and passages.
- **Passage**: retrieval unit; sized to a token budget, aligned to paragraph/list/table/code boundaries.
- **Anchor**: an opaque `anchor_ref` that can be resolved to a source location.
- **Doc version**: a stable identifier representing a specific content snapshot (exact mechanism depends on ingestion; e.g., content hash or (source_ref, updated_at)).

## 6. Requirements and Invariants
### 6.1 Hard invariants

1. **Stable identity**
   - `doc_id` stable across re-ingestion.
   - `segment_id` stable within a doc version.
2. **Anchorability**
   - every segment references an anchor that resolves to the source.
3. **Hierarchical integrity**
   - parents form a DAG tree; no cycles.
4. **Determinism**
   - parser + segmenter produce identical outputs for identical inputs.

### 6.2 Segment-level requirements for RAG

- **Topical coherence**: avoid mixing multiple unrelated topics inside one passage.
- **Structural coherence**: avoid splitting inside tables, code blocks, list items (unless necessary).
- **Context sufficiency**: each passage should be understandable without excessive external context; where unavoidable, overlap and/or neighbor expansion should compensate.
- **Budget compatibility**: passage sizes support efficient retrieval and assembly for the assistant's context window.

## 7. Segment Output Contract (Schema)
### 7.1 Segment record

```json
{
  "segment_id": "string",
  "doc_id": "string",
  "type": "SECTION|PASSAGE",
  "parent_id": "string|null",
  "section_path": "H1>H2>...",
  "anchor": "anchor_ref",
  "text": "string",
  "token_count": 123,
  "metadata": {
    "block_types": ["para","table"],
    "language": "python"
  }
}
```

### 7.2 Required fields by segment type

- `SECTION`:
  - required: `segment_id`, `doc_id`, `type`, `section_path`, `anchor`
  - `parent_id` may be null (top-level) or point to another SECTION (nested headings)
  - `text` may be empty or a normalized "section summary text" depending on product needs; for v1, set to concatenation of contained blocks or a minimal header context (decision).
- `PASSAGE`:
  - required: `segment_id`, `doc_id`, `type`, `parent_id` (must point to SECTION), `anchor`, `text`, `token_count`

### 7.3 Referential integrity rules

- every `PASSAGE.parent_id` must refer to an existing SECTION in the same output.
- `section_path` must match a node in the parser's heading tree (or a deterministic synthesized path for heading-less docs).

## 8. Configuration Surface

Minimum configuration (defaults shown):

```yaml
parsing:
  preserve_tables: true
  preserve_code_blocks: true

segmentation:
  passage_tokens_target: 600
  passage_tokens_min: 300
  passage_tokens_max: 900
  overlap_ratio: 0.10      # 0.0 - 0.15
  # Optional advanced knobs (v1 may defer):
  prefer_paragraph_boundaries: true
  avoid_mid_sentence_splits: true
  max_table_tokens: 1200
  max_code_tokens: 1200
  language_detection: simple # "simple" | "fasttext" (TBD)
```

Token counts must be computed with a tokenizer compatible with the embedding model (or a validated proxy), and must be consistent across runs.

## 9. Identity and Anchoring
### 9.1 Anchor model

Anchors are opaque references returned by the parser/distiller and must be resolvable by clients.

Segmenter responsibilities:

- choose the correct anchor for each segment:
  - `SECTION`: section anchor (`sec_anchor`) derived from heading path or stable IDs
  - `PASSAGE`: passage anchor (`pass_anchor`) derived from section + offset range

### 9.2 Deterministic segment_id construction (v1)

Goal: stable within a doc version; reproducible.

**Recommended v1 scheme:**

- Define a `doc_version_id` (content hash or stable ingestion version).
- Construct deterministic IDs via a cryptographic hash of stable inputs:

```
segment_id = HASH(
  doc_id
  + doc_version_id
  + type
  + section_path
  + anchor_ref
  + span_signature   # e.g., (start_offset, end_offset) in canonical_text
)
```

Notes:

- `anchor_ref` should already encode section + offsets; if so, `span_signature` may be redundant but helps guard against anchor format drift.
- For `SECTION`, use the section anchor and optionally a stable heading signature (normalized heading text + level).

### 9.3 Traceability across versions (v1 "good enough")

When a doc changes, some segment IDs will change. We still want "traceability" for analytics and debugging.

**Approach:**

- Maintain a `segment_lineage` record in metadata store (optional but recommended):
  - `old_segment_id` -> `new_segment_id` mapping when similarity exceeds threshold.
- Similarity can be computed from:
  - anchor overlap (same section_path + overlapping offset ranges)
  - text similarity (e.g., token Jaccard / MinHash / cosine of cheap embedding)
- Track churn metrics (see §16).

This is not required for core retrieval, but is important for operational stability and interpreting eval deltas.

## 10. Segmentation Policy (Core Logic)
### 10.1 Hierarchy construction

1. Build SECTION nodes from the heading tree:
   - each heading defines a SECTION boundary
   - nested headings produce nested SECTION parents (or flatten to section_path; decision in §19)
2. For each SECTION, collect ordered content blocks from the parser:
   - paragraphs
   - lists (as list-item blocks)
   - tables (atomic blocks)
   - code blocks (atomic blocks)

### 10.2 Passage chunking rules

- Passages are created **within a SECTION**.
- Target size in tokens: `passage_tokens_target` (default 600).
- Hard bounds: `[passage_tokens_min, passage_tokens_max]` (default 300-900).
- Overlap: `overlap_ratio` of tokens (default 10%), applied only at safe boundaries.

**Preferred cut boundaries (highest to lowest preference):**

1. Between blocks (paragraph/list/table/code)
2. Between list items (if list block is too large)
3. Between sentences (if paragraph too large)
4. Last resort: token boundary (avoid unless unavoidable)

**Never split inside:**

- table header row (must be repeated if table is split)
- code tokens that would break syntax *when avoidable* (use logical boundaries first)

### 10.3 Special handling: tables

- If table `token_count ≤ max_table_tokens`:
  - emit as a single PASSAGE (even if above `passage_tokens_max`) and mark `block_types: ["table"]`.
- Else:
  - split into row groups.
  - repeat header row for each split.
  - choose row-group sizes to stay near `passage_tokens_target` (allow larger if header dominates).

### 10.4 Special handling: code blocks

- If code `token_count ≤ max_code_tokens`:
  - emit as a single PASSAGE and mark language.
- Else:
  - attempt logical splitting by:
    - function/class boundaries (prefer Tree-sitter if available)
    - otherwise heuristic boundaries:
      - `def`, `class`, `{}` blocks, or blank-line separated regions
  - preserve minimal context:
    - keep imports/header with first split where possible
    - repeat key signatures if required (decision)

### 10.5 Lists and procedures

- Treat each list item as an atomic unit when feasible.
- For very long lists:
  - split between items into multiple passages.
  - keep the list header/intro sentence with each split if possible.

### 10.6 Overlap strategy

Overlap is intended to improve recall for boundary queries without excessive duplication.

- Compute overlap in tokens from the end of the previous passage.
- Apply overlap only if it can be aligned to a safe boundary (block boundary or sentence boundary).
- Record overlap metadata (optional):
  - `metadata.overlap_from_segment_id`
  - `metadata.overlap_token_count`

## 11. Reference Algorithm (Pseudocode)

```python
def segment_section(section, blocks, cfg, tokenizer):
    passages = []
    cur = []
    cur_tokens = 0

    def flush():
        nonlocal cur, cur_tokens
        if not cur:
            return
        text = serialize(cur)
        passages.append(text)
        cur = []
        cur_tokens = 0

    for block in blocks:
        b_text = serialize([block])
        b_tokens = tokenizer.count(b_text)

        if block.type in ("table", "code"):
            for piece in split_special(block, cfg, tokenizer):
                if cur_tokens >= cfg.passage_tokens_min:
                    flush()
                passages.append(piece.text)
            continue

        if cur_tokens + b_tokens <= cfg.passage_tokens_target:
            cur.append(block)
            cur_tokens += b_tokens
            continue

        if cur_tokens >= cfg.passage_tokens_min:
            flush()
            cur.append(block)
            cur_tokens = b_tokens
        else:
            parts = split_block(block, cfg, tokenizer)
            for p in parts:
                p_tokens = tokenizer.count(p)
                if cur_tokens + p_tokens > cfg.passage_tokens_target and cur_tokens >= cfg.passage_tokens_min:
                    flush()
                cur.append(p)
                cur_tokens += p_tokens

    flush()
    return apply_overlap(passages, cfg, tokenizer)
```

This pseudocode is a behavioral sketch; the production implementation must preserve anchors/spans and output full segment objects.

## 12. Retrieval + Context Assembly (RAG Integration)
### 12.1 Indexing strategy

Minimum v1:

- embed and index `PASSAGE` segments (required)

Optional (recommended if budget allows):

- also embed `SECTION` segments to enable coarse retrieval and hierarchical narrowing.

### 12.2 Hierarchical retrieval patterns enabled by segmentation

**Pattern A (passage-first + expansion):**

1. retrieve top-k PASSAGE by vector similarity
2. rerank (cross-encoder or LLM reranker)
3. expand context by:
   - adding adjacent passages (prev/next) within same section_path
   - optionally adding section header text
4. assemble final context under token budget

**Pattern B (section-first + within-section selection):**

1. retrieve top-k SECTION vectors
2. within selected sections, retrieve/rerank passages
3. assemble context preserving section order

### 12.3 Context assembly rules

- Maintain stable ordering by `(section_path, passage_offset)`.
- Deduplicate overlap:
  - if passages share ≥ X% overlap, keep highest-scoring and expand via neighbors instead.
- Avoid "context spam":
  - cap number of passages per section unless scores justify.
- Citation:
  - cite passage anchors for specific claims
  - optionally include section anchor when summarizing broader content

## 13. Quality Definition and Measurement

Quality is defined at three layers: **intrinsic segmentation**, **retrieval relevance**, and **end-to-end assistant outcomes**.

### 13.1 Intrinsic segmentation quality (fast gates)

These are cheap checks that run on every build.

**Length and structure**

- ≥ 95% of non-table/non-code passages have token_count within `[min, max]`.
- mid-sentence split rate ≈ 0 (allow exceptions only where unavoidable).
- empty passage rate = 0.
- orphan passage rate low: passages beginning with unresolved pronouns/determiners (proxy measure).

**Structure preservation**

- table header present in every table-split piece.
- code blocks not split mid-token; syntax break rate measured if parsers exist.

**Determinism**

- hash of segment outputs identical across repeated runs.

### 13.2 Retrieval quality (offline IR eval)

Construct a labeled set of queries with known relevant spans (can be curated from:

- support tickets
- runbooks
- docs Q&A
- incident retrospectives)

Metrics:

- Recall@k: does top-k contain a passage overlapping the gold span?
- MRR@k / nDCG@k: ranking quality with graded relevance.
- Evidence coverage: % of required facts contained in retrieved set.

### 13.3 End-to-end assistant quality (offline)

For a fixed evaluation suite (query -> expected facts -> gold citations):

- Answer correctness (rubric or exact-match/F1 where feasible)
- Faithfulness / groundedness:
  - every claim supported by retrieved evidence
  - "unsupported claim" rate
- Citation precision:
  - cited anchor actually contains the asserted evidence
- Abstention behavior:
  - when evidence absent, assistant declines or requests clarification

### 13.4 Online monitoring (post-launch)

- user feedback: helpfulness / follow-up rate / query reformulations
- citation click outcomes (proxy for anchor correctness)
- retrieval debug stats:
  - duplicate overlap ratio
  - truncation rate
  - per-section dominance (one section crowding context)

## 14. Acceptance Criteria (Ship Gates)
### 14.1 Functional correctness

- every PASSAGE has `doc_id`, `segment_id`, `anchor`, and `parent_id` (section)
- referential integrity: no orphaned parents/children
- anchor resolution passes on sampled segments

### 14.2 Quality gates

- intrinsic gates pass on representative corpus (format diversity)
- retrieval offline eval: not worse than baseline and ideally improves:
  - Recall@k (primary) and nDCG/MRR (secondary)
- end-to-end eval: improves citation accuracy and reduces unsupported-claim rate

### 14.3 Performance gates (v1)

- segmenter runtime within acceptable ingestion budgets (TBD)
- memory footprint stable (TBD)

## 15. Testing Plan
### 15.1 Golden corpus

Maintain a fixed corpus of representative docs:

- markdown/html/wiki pages
- PDFs with tables
- code-heavy docs
- runbooks and incident docs with step lists and error codes

### 15.2 Test types

- Unit tests:
  - boundary selection
  - special split logic (tables/code/lists)
  - ID determinism
- Snapshot ("golden") tests:
  - exact segment list comparison for fixed inputs
- Property tests:
  - no empty text
  - token_count non-negative
  - stable ordering
- Anchor resolution tests:
  - randomly sample segments and validate anchor -> correct offset/render position

### 15.3 Regression workflow

- Any change to segmentation logic must run:
  - intrinsic gates
  - offline retrieval eval
  - churn analysis on versioned docs

## 16. Observability and Metrics

Emit pipeline-level events plus segmenter-specific counters.

### 16.1 Core event vocabulary

- `DocFetched(doc_id, updated_at)`
- `DocParsed(doc_id, anchors_count, structure_nodes)`
- `DocSegmented(doc_id, sections, passages)`
- `EmbeddingsCreated(doc_id, count, model_version)`
- `Published(doc_id, upserts, tombstones)`
- `PipelineError(stage, doc_id, error_class)`

### 16.2 Segmenter metrics

- passage token_count histogram (p50/p90/p99)
- mid-sentence split rate
- table/code atomic vs split counts
- overlap duplication ratio
- churn:
  - % segments changed per doc update
  - % stable IDs retained after small edits

## 17. Rollout Plan

1. **Shadow mode**:
   - generate segments and metrics; do not affect retrieval.
2. **Offline evaluation**:
   - compare against baseline chunking on labeled set.
3. **Dual-index experiment** (optional):
   - index both baseline and new passages; route small traffic slice to new retrieval.
4. **A/B rollout**:
   - monitor online metrics and rollback triggers.
5. **Backfill + incremental refresh**:
   - re-segment and re-embed by doc source priority; publish idempotent upserts + tombstones.

Rollback trigger examples:

- significant drop in offline retrieval metrics
- increase in unsupported-claim rate
- anchor resolution errors above threshold

## 18. Risks and Mitigations

- **Over-splitting** (loss of coherence):
  - enforce min token threshold; avoid mid-sentence splits; use neighbor expansion.
- **Under-splitting** (budget inefficiency):
  - enforce max thresholds except for atomic table/code; consider splitting large sections.
- **Duplicate evidence due to overlap**:
  - tune overlap and dedup in context builder; track duplicate ratio.
- **ID churn on minor edits**:
  - stabilize span/anchor-based IDs; maintain lineage mapping; track churn.
- **Table/code edge cases**:
  - robust serializers; header repetition; safe splits; dedicated tests.

## 19. Open Decisions / TODOs

1. **SECTION text representation (v1)**:
   - empty vs header-only vs concatenated text (affects SECTION embedding usefulness).
2. **Nested SECTION graph shape**:
   - strict tree vs flattened section_path with parent pointers.
3. **Tokenizer choice**:
   - exact embedding tokenizer vs proxy; ensure determinism.
4. **Code splitting implementation**:
   - Tree-sitter dependency (supported languages?) vs heuristics only.
5. **Anchor format and resolution contract**:
   - source-specific fragments vs canonical offsets; define resolver interface.
6. **Overlap defaults per corpus**:
   - 0-15% allowed; choose default by eval.
7. **Dual-index strategy**:
   - SECTION+PASSAGE embeddings vs PASSAGE only (cost vs benefit).
8. **Traceability implementation**:
   - lineage mapping storage and matching thresholds.

## Appendix A: Baseline Comparison Plan (Template)

- Baseline chunker:
  - (describe current approach: token size, overlap, structure awareness)
- Proposed segmenter v1:
  - SECTION boundaries + structure-aware passage chunking
- Offline eval:
  - dataset description and metrics
- Decision rule:
  - ship if Recall@k improves by ≥ X% and unsupported-claim rate decreases by ≥ Y% (TBD)
