Good. I would turn this into a **two-layer test plan**:

1. **PR1 contract layer** — state machine, lifecycle runtime models, compatibility seam.
2. **MVP lifecycle layer** — stage runners, persistence, retries, readiness, and a small number of real end-to-end fixtures.

That matches the docs: internal lifecycle contracts are the center of gravity, stage boundaries must correspond to persisted evidence, retries are document-scoped, and `READY` is a strict predicate over persisted artifacts plus a real retrieval smoke call.  

## Test package shape

I would lay it out like this:

```text
tests/
  contract/
    test_processing_status_sets.py
    test_lifecycle_state_machine.py
    test_lifecycle_models.py
    test_contract_seam_compat.py
    test_readiness_contract.py

  stages/
    test_register_stage.py
    test_extract_stage_markdown.py
    test_extract_stage_pdf.py
    test_normalize_stage_markdown.py
    test_normalize_stage_pdf.py
    test_section_stage.py
    test_chunk_stage.py
    test_index_stage.py
    test_ready_stage.py

  persistence/
    test_document_repository.py
    test_section_repository.py
    test_chunk_repository.py
    test_index_entry_repository.py
    test_replace_on_retry.py
    test_integrity_constraints.py
    test_lifecycle_event_persistence.py

  artifacts/
    test_raw_artifact_store.py
    test_extracted_artifact_store.py
    test_normalized_artifact_store.py
    test_normalized_payload_regressions.py

  pipeline/
    test_markdown_to_ready.py
    test_pdf_to_ready.py
    test_pdf_failure_paths.py
    test_unsupported_inputs.py
    test_retry_recovery.py
    test_readiness_smoke.py

  fixtures/
    docs/
      simple.md
      handbook.md
      text_layer_ok.pdf
      sparse_text_layer.pdf
      malformed.pdf
      unsupported.png
```

That split follows the architecture doc directly: contract tests, persistence tests, artifact tests, pipeline tests, and smoke retrieval tests are all explicitly called out. 

## Shared fixture strategy

I would keep the fixture model very deliberate so tests stay fast and composable.

### Core factories

```python
@pytest.fixture
def document_factory():
    def make(**overrides) -> Document:
        base = dict(
            doc_id="doc_123",
            workspace_id="ws_1",
            source_type="markdown",
            title="Test Doc",
            filename="test.md",
            checksum="sha256:abc",
            uploaded_at=datetime(2026, 3, 10, 12, 0, 0),
            raw_storage_path="data/raw/ws_1/doc_123/source.md",
            status=ProcessingStatus.REGISTERED,
            current_job_id=None,
            failure_code=None,
            failure_detail=None,
        )
        base.update(overrides)
        return Document(**base)
    return make
```

```python
@pytest.fixture
def normalized_payload_factory():
    def make(doc_id="doc_123", source_type="markdown", blocks=None, **stats):
        return NormalizedPayload(
            doc_id=doc_id,
            source_type=source_type,
            blocks=blocks or [],
            stats=stats or {"block_count": len(blocks or [])},
        )
    return make
```

```python
@pytest.fixture
def section_factory():
    def make(**overrides) -> Section:
        base = dict(
            section_id="sec_1",
            doc_id="doc_123",
            parent_section_id=None,
            heading_path=["Intro"],
            heading_text="Intro",
            ordinal=0,
            page_start=None,
            page_end=None,
            block_start=0,
            block_end=3,
            source_offset_start=0,
            source_offset_end=200,
        )
        base.update(overrides)
        return Section(**base)
    return make
```

```python
@pytest.fixture
def chunk_factory():
    def make(**overrides) -> Chunk:
        base = dict(
            chunk_id="chk_1",
            doc_id="doc_123",
            section_id="sec_1",
            ordinal=0,
            heading_path=["Intro"],
            text="hello world",
            token_count=2,
            page_start=None,
            page_end=None,
            block_start=0,
            block_end=1,
            source_offset_start=0,
            source_offset_end=11,
        )
        base.update(overrides)
        return Chunk(**base)
    return make
```

### Backing fixtures

I would use three backing styles:

* **pure in-memory fakes** for state machine, stage logic, and readiness predicate unit tests
* **real temp filesystem** for artifact persistence tests
* **real Postgres test DB** for repository, replace-on-retry, and pipeline tests

That is consistent with the design’s filesystem/Postgres split and the emphasis on persisted evidence, linkage, and inspectability. 

### Service fakes

You want deterministic fakes for everything expensive or external:

```python
class FakeArtifactStore:
    ...
class FakeExtractionService:
    ...
class FakeNormalizationService:
    ...
class FakeVectorIndex:
    ...
class DeterministicEmbeddingAdapter:
    ...
```

The one fake I would keep slightly realistic is `FakeVectorIndex.smoke_query()`, because the docs require a real queryable retrieval call at readiness time. Even in unit tests, the fake should behave like an actual query API rather than a boolean flag. 

## Contract tests

These should be the first files written.

### `test_processing_status_sets.py`

Purpose: prove the canonical status sets and terminal/in-flight partition.

Named tests:

* `test_in_flight_statuses_are_registered_through_indexed`
* `test_terminal_statuses_are_ready_and_failed`
* `test_uploaded_is_not_in_flight_terminal_overlap`
* `test_status_sets_are_disjoint`

### `test_lifecycle_state_machine.py`

Purpose: linear lifecycle contract plus rejection of illegal moves.

Named tests:

* `test_linear_happy_path_transitions_are_allowed`
* `test_failed_reachable_from_each_in_flight_status`
* `test_uploaded_to_failed_is_rejected`
* `test_skip_transition_is_rejected`
* `test_regression_from_terminal_state_is_rejected`
* `test_ready_is_terminal_without_reingest_model`

The `UPLOADED -> FAILED` rejection is specifically required by PR1. 

Example:

```python
@pytest.mark.parametrize(
    ("src", "dst"),
    [
        (ProcessingStatus.UPLOADED, ProcessingStatus.REGISTERED),
        (ProcessingStatus.REGISTERED, ProcessingStatus.EXTRACTING),
        (ProcessingStatus.EXTRACTING, ProcessingStatus.NORMALIZED),
        (ProcessingStatus.NORMALIZED, ProcessingStatus.CHUNKED),
        (ProcessingStatus.CHUNKED, ProcessingStatus.INDEXED),
        (ProcessingStatus.INDEXED, ProcessingStatus.READY),
    ],
)
def test_linear_happy_path_transitions_are_allowed(src, dst):
    assert is_valid_transition(src, dst)
```

```python
@pytest.mark.parametrize(
    ("src", "dst"),
    [
        (ProcessingStatus.UPLOADED, ProcessingStatus.FAILED),
        (ProcessingStatus.REGISTERED, ProcessingStatus.CHUNKED),
        (ProcessingStatus.READY, ProcessingStatus.CHUNKED),
        (ProcessingStatus.FAILED, ProcessingStatus.READY),
    ],
)
def test_illegal_transitions_are_rejected(src, dst):
    with pytest.raises(InvalidLifecycleTransitionError):
        validate_transition(src, dst)
```

### `test_lifecycle_models.py`

Purpose: storage-independent runtime lifecycle types introduced in PR1.

Named tests:

* `test_lifecycle_event_requires_stage_and_to_status`
* `test_lifecycle_stage_enum_values_are_stable`
* `test_failure_category_enum_covers_expected_failure_classes`
* `test_lifecycle_event_detail_defaults_to_mapping`
* `test_runtime_models_are_internal_not_contract_models`

That matches the PR1 requirement to add focused lifecycle model tests. 

### `test_contract_seam_compat.py`

Purpose: prove `_contracts` remains a compatibility boundary.

Named tests:

* `test_contract_processing_status_reexports_runtime_status`
* `test_contract_transition_helpers_match_runtime_helpers`
* `test_existing_import_sites_remain_valid`
* `test_contract_document_model_unchanged_in_pr1`

That last one matters because PR1 explicitly says not to rename fields or create a parallel domain layer there. 

## Readiness contract tests

This is the most important contract beyond the state machine.

### `test_readiness_contract.py`

Named tests:

* `test_ready_requires_document_record`
* `test_ready_requires_normalized_artifact`
* `test_ready_requires_nonzero_sections`
* `test_ready_requires_nonzero_chunks`
* `test_ready_requires_index_count_equal_chunk_count`
* `test_ready_requires_valid_chunk_owner_links`
* `test_ready_requires_minimum_provenance`
* `test_ready_requires_retrieval_smoke_pass`
* `test_ready_rejected_when_open_failure_present`

That is just the recommended readiness predicate turned into tests. The docs define `READY` as a strict conjunction over persisted artifacts, intact linkage, provenance minimums, and a real smoke query. 

Example:

```python
def test_ready_requires_index_count_equal_chunk_count(readiness_service, seeded_doc):
    seeded_doc.normalized_exists = True
    seeded_doc.section_count = 2
    seeded_doc.chunk_count = 3
    seeded_doc.index_count = 2
    seeded_doc.owner_links_valid = True
    seeded_doc.provenance_valid = True
    seeded_doc.smoke_passes = True

    assert readiness_service.evaluate(doc_id=seeded_doc.doc_id) is False
```

## Stage-runner tests

Each stage test should assert:

1. precondition status is validated
2. work result is persisted
3. lifecycle event is emitted
4. next stage is queued on success
5. status does not advance if persistence/invariant checks fail

That maps directly to the stage runner contract in the architecture doc. 

### `test_register_stage.py`

Named tests:

* `test_register_stage_creates_document_with_stable_identity`
* `test_register_stage_persists_raw_artifact_linkage`
* `test_register_stage_appends_lifecycle_event`
* `test_register_stage_enqueues_extract_job`
* `test_register_stage_is_idempotent_for_same_upload_context`
* `test_register_stage_records_failure_on_repository_error`

### `test_extract_stage_markdown.py`

Named tests:

* `test_markdown_extract_preserves_order_exactly`
* `test_markdown_extract_preserves_code_fences`
* `test_markdown_extract_records_offsets_when_available`
* `test_extract_stage_persists_extracted_artifact_before_advance`
* `test_extract_stage_fails_on_decode_error`

### `test_extract_stage_pdf.py`

Named tests:

* `test_pdf_extract_preserves_page_boundaries`
* `test_pdf_extract_records_warnings_for_sparse_text_layer`
* `test_pdf_extract_rejects_no_recoverable_text_layer`
* `test_pdf_extract_fails_on_malformed_pdf`
* `test_extract_stage_does_not_mark_extracted_without_artifact`

The docs are explicit: PDF is text-layer-only, no OCR, page boundaries preserved when possible, warnings captured for sparse or malformed text.

### `test_normalize_stage_markdown.py`

Named tests:

* `test_markdown_normalize_recovers_heading_blocks`
* `test_markdown_normalize_preserves_code_block_boundaries`
* `test_markdown_normalize_preserves_paragraph_boundaries`
* `test_markdown_normalize_persists_payload_before_status_advance`

### `test_normalize_stage_pdf.py`

Named tests:

* `test_pdf_normalize_preserves_page_transition_blocks`
* `test_pdf_normalize_promotes_heading_only_above_confidence_threshold`
* `test_pdf_normalize_keeps_uncertain_heading_as_paragraph`
* `test_pdf_normalize_allows_synthetic_structure_fallback`
* `test_pdf_normalize_never_claims_unrecovered_layout_semantics`

That last one is directly aligned with the “conservative structure over fabricated structure” principle. 

### `test_section_stage.py`

Named tests:

* `test_section_derivation_from_markdown_headings_creates_valid_tree`
* `test_pdf_section_derivation_uses_inferred_headings_when_present`
* `test_pdf_section_derivation_creates_synthetic_sections_when_headings_sparse`
* `test_every_section_has_non_empty_heading_path`
* `test_section_order_matches_normalized_block_order`

### `test_chunk_stage.py`

Named tests:

* `test_chunking_prefers_section_boundaries_over_fixed_windows`
* `test_chunking_keeps_code_blocks_intact_when_possible`
* `test_chunking_avoids_crossing_major_heading_boundaries`
* `test_chunking_adds_required_metadata_fields`
* `test_chunking_enforces_owner_link_integrity_before_chun​​ked`
* `test_chunking_replaces_existing_document_chunk_set_on_retry`

The docs explicitly require no orphan chunks, stable ordering, document/section ownership, and replace-on-retry semantics. 

### `test_index_stage.py`

Named tests:

* `test_index_stage_publishes_every_active_chunk`
* `test_index_stage_persists_index_entries`
* `test_index_stage_deletes_or_replaces_prior_entries_on_retry`
* `test_index_stage_requires_index_entry_count_to_match_chunk_count`
* `test_index_stage_fails_when_vector_upsert_partial`

### `test_ready_stage.py`

Named tests:

* `test_ready_stage_sets_ready_only_when_readiness_service_passes`
* `test_ready_stage_does_not_mask_open_failure`
* `test_ready_stage_appends_final_lifecycle_event`
* `test_ready_stage_uses_real_query_interface_for_smoke_check`

## Persistence tests

These should use real DB constraints, not mocks.

### `test_document_repository.py`

Named tests:

* `test_create_and_get_document_round_trip`
* `test_update_status_persists_failure_code_and_detail`
* `test_document_status_update_is_atomic`

### `test_section_repository.py`

Named tests:

* `test_replace_for_document_removes_prior_sections`
* `test_sections_round_trip_preserves_parent_child_links`
* `test_sections_are_unique_by_section_id`

### `test_chunk_repository.py`

Named tests:

* `test_replace_for_document_removes_prior_chunks`
* `test_chunk_round_trip_preserves_section_link`
* `test_chunk_cannot_reference_missing_section`
* `test_chunk_ordering_round_trip_is_stable`

### `test_index_entry_repository.py`

Named tests:

* `test_index_entries_match_active_chunk_set`
* `test_index_entry_requires_existing_chunk`
* `test_delete_and_republish_for_document_is_safe`

### `test_replace_on_retry.py`

Named tests:

* `test_retry_from_normalized_replaces_sections_and_chunks`
* `test_retry_from_chunked_replaces_index_entries`
* `test_double_retry_is_idempotent`
* `test_retry_does_not_duplicate_child_ownership`

### `test_integrity_constraints.py`

Named tests:

* `test_no_orphan_chunks_possible`
* `test_no_chunk_without_document_possible`
* `test_no_section_without_document_possible`
* `test_ready_document_must_have_linked_artifacts`

That all follows the repo interfaces and the explicit integrity requirements in the architecture doc. 

## Artifact tests

These catch regressions that don’t show up as status failures immediately.

### `test_normalized_payload_regressions.py`

Named tests:

* `test_normalized_payload_preserves_original_order`
* `test_markdown_fixture_expected_heading_block_sequence`
* `test_pdf_fixture_preserves_page_anchor_metadata`
* `test_ready_chunks_all_have_coarse_provenance`

The artifact tests are explicitly required: normalized order, Markdown hierarchy, PDF page anchors, and coarse provenance for ready chunks. 

## Pipeline tests

Keep these few but real.

### `test_markdown_to_ready.py`

Named tests:

* `test_simple_markdown_fixture_reaches_ready`
* `test_markdown_fixture_is_queryable_after_ready`
* `test_markdown_fixture_supports_source_navigation_fields`

### `test_pdf_to_ready.py`

Named tests:

* `test_text_based_pdf_fixture_reaches_ready`
* `test_pdf_fixture_ready_chunks_have_page_or_offset_provenance`
* `test_pdf_fixture_smoke_query_returns_own_document`

### `test_pdf_failure_paths.py`

Named tests:

* `test_malformed_pdf_reaches_failed_with_failure_detail`
* `test_sparse_text_layer_pdf_reaches_failed_or_stops_before_ready`
* `test_partial_pdf_artifacts_preserved_for_inspection`

### `test_unsupported_inputs.py`

Named tests:

* `test_png_is_rejected_explicitly`
* `test_scanned_pdf_without_text_layer_is_not_best_effort_processed`

### `test_retry_recovery.py`

Named tests:

* `test_retry_after_index_publication_failure_reaches_ready`
* `test_retry_after_chunk_failure_replaces_downstream_artifacts`
* `test_retry_preserves_document_identity`

Those pipeline cases are listed almost verbatim in the validation section.

## Fixture corpus

I would keep exactly six canonical fixtures at first:

### 1. `simple.md`

Small clean headings, short paragraphs.

Use for:

* registration
* extract
* normalize
* section
* chunk
* readiness happy path

### 2. `handbook.md`

Nested headings, lists, fenced code blocks, long paragraph.

Use for:

* hierarchy derivation
* chunking boundaries
* code-block preservation
* source offsets

### 3. `text_layer_ok.pdf`

Real text-based PDF with headings and page boundaries.

Use for:

* PDF happy path
* page provenance
* conservative heading inference

### 4. `sparse_text_layer.pdf`

Technically parseable but low-quality text layer.

Use for:

* extraction warnings
* normalization fallback
* failure vs degraded behavior boundary

### 5. `malformed.pdf`

Corrupted bytes or broken xref.

Use for:

* explicit extraction failure
* failure payload and inspectability

### 6. `unsupported.png`

Use for:

* explicit unsupported input rejection

This aligns with MVP input boundaries: only text-based PDFs and Markdown are in scope, OCR/scanned/image-centric flows are out. 

## Test markers

I would add markers immediately:

```toml
[tool.pytest.ini_options]
markers = [
  "contract: lifecycle semantics and invariants",
  "stage: individual stage runner behavior",
  "persistence: db-backed integrity and repository tests",
  "artifact: normalized/extracted payload regression tests",
  "pipeline: end-to-end ingest tests",
  "slow: real pdf/vector/db tests",
]
```

And then keep CI split as:

* fast path: `contract or stage`
* medium path: `persistence or artifact`
* slower nightly/pre-merge path: `pipeline and slow`

## First 15 tests I would actually write

In this order:

1. `test_linear_happy_path_transitions_are_allowed`
2. `test_uploaded_to_failed_is_rejected`
3. `test_failed_reachable_from_each_in_flight_status`
4. `test_ready_requires_index_count_equal_chunk_count`
5. `test_ready_requires_minimum_provenance`
6. `test_register_stage_creates_document_with_stable_identity`
7. `test_extract_stage_persists_extracted_artifact_before_advance`
8. `test_markdown_normalize_persists_payload_before_status_advance`
9. `test_every_section_has_non_empty_heading_path`
10. `test_chunking_enforces_owner_link_integrity_before_chunked`
11. `test_replace_for_document_removes_prior_chunks`
12. `test_index_stage_publishes_every_active_chunk`
13. `test_markdown_fixture_reaches_ready`
14. `test_malformed_pdf_reaches_failed_with_failure_detail`
15. `test_retry_after_index_publication_failure_reaches_ready`

That sequence gives you the highest-value invariants first: state correctness, readiness honesty, persistence honesty, then one happy path and one ugly path.

## What I would not do yet

I would not spend time on:

* broad HTTP endpoint testing
* snapshotting large full artifacts indiscriminately
* many PDF layout edge cases
* property-based fuzzing before the core invariants are stable

The docs are explicit that transport is not the architectural center and that PDF understanding is intentionally conservative in MVP.

## Sharp recommendation

If you want maximum signal with minimum effort, implement this slice first:

* `test_lifecycle_state_machine.py`
* `test_readiness_contract.py`
* `test_chunk_stage.py`
* `test_replace_on_retry.py`
* `test_markdown_to_ready.py`
* `test_pdf_failure_paths.py`
* `test_contract_seam_compat.py`

That gives you coverage over the main trust contract: legal lifecycle progression, honest `READY`, no duplicate child ownership on retry, one representative success case, one representative failure case, and PR1 seam stability.

I can turn this into a concrete `pytest` starter scaffold with `conftest.py`, markers, and 8-10 initial test files.
