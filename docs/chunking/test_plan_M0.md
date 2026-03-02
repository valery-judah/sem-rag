# M0 Test Plan: Anchored Flat Passages

Based on the RFC and Refactored User Stories, the simplest test set to start with should focus exclusively on **M0** ("Anchored flat passages - minimum viable segmentation"). This defers hierarchy, budgets, IDs, and complex splitting to later milestones.

## Objective

Validate that we can emit `PASSAGE` segments from a simulated parsed document, ensuring foundational invariants: text resolution (anchorability) and no empty chunks.

## Proposed M0 Test Cases (`tests/test_segmentation.py`)

1. **`test_passage_text_resolves_to_offsets` (US3.2)**
   - **Scenario**: Pass a simple `canonical_text` and a mock block to the segmenter.
   - **Assertion**: For every emitted passage, `canonical_text[segment.start_char_offset : segment.end_char_offset] == segment.text`.

2. **`test_no_empty_passages_emitted` (US1.3 / US5.1)**
   - **Scenario**: Provide an input containing empty strings or whitespace-only blocks.
   - **Assertion**: The segmenter filters them out. Emitted passages strictly have `len(segment.text.strip()) > 0`.

3. **`test_offsets_strictly_in_bounds` (US5.1)**
   - **Scenario**: Pass a standard input document.
   - **Assertion**: `0 <= segment.start_char_offset < segment.end_char_offset <= len(canonical_text)`.

4. **`test_segment_type_is_passage`**
   - **Scenario**: Basic input block.
   - **Assertion**: Emitted segments have `type = "PASSAGE"`.

## Development Steps

1. Define a minimal data model in `src/docforge/segmentation.py` (e.g., `Segment`, `Passage` with `type`, `text`, `start_char_offset`, `end_char_offset`).
2. Write `tests/test_segmentation.py` implementing the cases above.
3. Implement a naive `segment_document()` function that passes the tests.
4. Run `make test`, `make type`, and `make lint` to verify.
