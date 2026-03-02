# User Stories: Hierarchical Segmentation for Full RAG Assistant

This document translates the requirements from the [Hierarchical Segmentation RFC](./hierarchical_segmentation_rfc.md) into actionable User Stories grouped by Epic.

---

## Epic 1: Core Segmentation & Hierarchy
*Objective: Build the foundational segmentation pipeline that breaks parsed documents into an acyclic `SECTION -> PASSAGE` hierarchy respecting token budgets and maintaining semantic coherence.*

**US1.1: Hierarchical Structuring**
- **As an** ingestion pipeline,
- **I want to** segment a parsed document's structural tree into nested `SECTION` nodes and leaf `PASSAGE` nodes,
- **So that** the retrieval system can fetch specific passages and expand them contextually using their parent sections.
- *Acceptance Criteria:*
  - Parents form a DAG/tree with no cycles.
  - Every `PASSAGE` has a valid `parent_id` linking it to a `SECTION`.
  - The `section_path` correctly reflects the headings in the parsed document structure tree.

**US1.2: Token Budget Constraints**
- **As an** ingestion pipeline,
- **I want to** enforce configurable minimum (e.g., 300), target (e.g., 600), and maximum (e.g., 900) token limits on passage size,
- **So that** passages fit efficiently into the vector store and LLM context window without being diluted or overly truncated.
- *Acceptance Criteria:*
  - Generated non-special passages fall within `[min, max]` token counts.
  - Token counts are computed consistently matching the target embedding model.

**US1.3: Boundary-Aware Splitting**
- **As an** ingestion pipeline,
- **I want to** prioritize splitting passages at safe semantic boundaries (between blocks, paragraphs, or sentences) rather than mid-sentence,
- **So that** passages remain semantically coherent for retrieval and synthesis.
- *Acceptance Criteria:*
  - Mid-sentence splits are minimized and only occur as a last resort (e.g., a single sentence exceeds the max token budget).
  - Empty passages are never generated.

**US1.4: Context Overlap**
- **As an** ingestion pipeline,
- **I want to** apply a configurable token overlap (e.g., 10%) between adjacent passages, aligning the overlap to safe boundaries,
- **So that** boundary queries retain sufficient context and recall is improved.
- *Acceptance Criteria:*
  - Overlap accurately captures text from the end of the previous passage.
  - Overlap breaks at block or sentence boundaries, not mid-word or mid-token.

---

## Epic 2: Structural Block Handling
*Objective: Preserve the semantics of specialized formatting (tables, code, lists) so they are fully interpretable by the RAG assistant.*

**US2.1: Small Table Preservation**
- **As an** ingestion pipeline,
- **I want to** keep tables that fit within the `max_table_tokens` limit as single, atomic passages (bypassing normal passage maximums if needed),
- **So that** tabular relationships remain completely intact for downstream reasoning.
- *Acceptance Criteria:*
  - Tables within limits are not split and are tagged with `block_types: ["table"]`.

**US2.2: Large Table Row-Splitting**
- **As an** ingestion pipeline,
- **I want to** split large tables by row groups while repeating the table header for each resulting passage,
- **So that** each segment provides sufficient self-contained context of what the table columns represent.
- *Acceptance Criteria:*
  - Split tables always include the original header row in every resulting passage.
  - Row groups are sized closely to the target token budget.

**US2.3: Logical Code Block Splitting**
- **As an** ingestion pipeline,
- **I want to** split large code blocks along logical boundaries (e.g., functions, classes, or heuristic spacing) while preserving imports and necessary signatures,
- **So that** code snippets remain syntactically valid and understandable when retrieved.
- *Acceptance Criteria:*
  - Code ≤ `max_code_tokens` is preserved atomically.
  - Code > `max_code_tokens` is split without breaking mid-token syntactically if at all possible.

**US2.4: List and Procedure Integrity**
- **As an** ingestion pipeline,
- **I want to** treat list items as atomic units and, when splitting long lists, repeat the list's introductory sentence or header for each passage,
- **So that** procedural steps are not orphaned from their intent.
- *Acceptance Criteria:*
  - Lists split across passages retain their context/header.
  - Individual list items are kept intact unless they exceed passage token maximums on their own.

---

## Epic 3: Identity, Anchoring & Traceability
*Objective: Ensure segments have stable identifiers and map accurately back to the original source location, maintaining consistency across re-ingestions.*

**US3.1: Deterministic Segment IDs**
- **As an** ingestion pipeline,
- **I want to** generate segment IDs deterministically based on document ID, version, structural path, anchor, and text span,
- **So that** parsing the identical document multiple times yields the exact same IDs.
- *Acceptance Criteria:*
  - Hashing logic guarantees identical output for identical input parameters.

**US3.2: Source Anchoring**
- **As a** citation renderer,
- **I want** every `SECTION` and `PASSAGE` to include an opaque `anchor_ref` that can be resolved back to a specific location in the source artifact,
- **So that** the user interface can display precise source citations.
- *Acceptance Criteria:*
  - Every segment object possesses a valid `anchor` field.
  - Anchors resolve successfully in citation render tests.

**US3.3: Incremental Churn Tracking (Traceability)**
- **As a** data scientist or operator,
- **I want to** maintain lineage mapping (`old_segment_id` -> `new_segment_id`) for segments whose text or boundaries shift slightly between document versions,
- **So that** I can track churn metrics and maintain stable citation references over time.
- *Acceptance Criteria:*
  - System generates similarity metrics between old and new segments.
  - Minor document edits do not result in a 100% loss of segment continuity.

---

## Epic 4: Retrieval & Context Assembly
*Objective: Enable downstream consumers to leverage the hierarchy to construct high-quality, relevant context windows.*

**US4.1: Vector Indexing for Passages**
- **As a** RAG retrieval orchestrator,
- **I want to** query embeddings of `PASSAGE` segments (and optionally `SECTION` segments) from a vector index,
- **So that** I can accurately find the most semantically relevant text spans for a user's query.

**US4.2: Context Expansion within Sections**
- **As a** RAG retrieval orchestrator,
- **I want to** expand a retrieved passage by fetching adjacent passages (prev/next) within the same `section_path`,
- **So that** the LLM receives comprehensive, coherent context rather than isolated snippets.
- *Acceptance Criteria:*
  - System can successfully query and return `passage_N-1` and `passage_N+1` given `passage_N`.

**US4.3: Overlap Deduplication and Ordering**
- **As a** context builder,
- **I want to** reorder retrieved passages by their structural offset and deduplicate heavily overlapping segments,
- **So that** the prompt assembled for the LLM is orderly, concise, and avoids redundant token usage.
- *Acceptance Criteria:*
  - Context blocks maintain stable ordering `(section_path, passage_offset)`.
  - Passages sharing ≥ X% overlap are deduplicated or merged intelligently.

---

## Epic 5: Quality Gates & Evaluation
*Objective: Quantify and ensure the semantic and structural quality of the chunking rules via offline metrics before deploying.*

**US5.1: Intrinsic Quality Gates**
- **As an** AI engineer,
- **I want** the segmenter pipeline to execute fast structural assertions (e.g., token bounds, empty passage checks, table header presence) on every build,
- **So that** blatant segmentation bugs are caught before embedding.
- *Acceptance Criteria:*
  - Pipeline fails if mid-sentence split rates or empty passage rates exceed strict thresholds.

**US5.2: Offline Retrieval Evaluation (IR Eval)**
- **As an** AI engineer,
- **I want to** measure Recall@k, MRR@k, and evidence coverage using a golden dataset of known queries and relevant spans,
- **So that** I can objectively prove the new hierarchical segmenter outperforms baseline flat chunking.
- *Acceptance Criteria:*
  - Recall@k metrics are recorded and show no regression compared to the flat chunking baseline.

**US5.3: End-to-End Faithfulness Evaluation**
- **As an** AI engineer,
- **I want to** run a complete evaluation suite to measure citation accuracy, answer correctness, and unsupported-claim rates,
- **So that** I know the segments produce safer and more accurate final RAG answers.
- *Acceptance Criteria:*
  - The rate of "unsupported claims" is reduced compared to baseline.
  - Citation precision improves compared to baseline.
