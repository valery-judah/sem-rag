# PR4 Implementation Plan: Ranges, Anchors, and Edge Policies

This document outlines the implementation plan for PR4, addressing the requirements set forth in the RFC (`docs/features/parsers/01_rfc.md`) and the Workplan (`docs/features/parsers/04_workplan.md`).

## 1. Architectural Breakdown

PR4 introduces two new specialized modules to the parser package. By decoupling range resolution and anchor generation from the core AST traversal, we ensure that these concerns can be unit-tested independently and swapped if hashing or canonicalization policies evolve.

### `src/docforge/parsers/ranges.py`
**Responsibility:** Deriving byte-exact (or character-exact) `[start, end]` spans for every structural block within the `canonical_text`.
**Key Components:**
- `RangeTracker`: A utility class that tracks the current offset during the tokenization of the `canonical_text` string.
- `resolve_ranges(tree: DocNode, canonical_text: str) -> None`: A function that validates and applies the derived ranges to the tree's blocks, ensuring all bounds are `0 <= start <= end <= len(canonical_text)`.

### `src/docforge/parsers/anchors.py`
**Responsibility:** Hashing and assigning deterministic identifiers for the document, its sections, and its structural passages.
**Key Components:**
- `HeadingNormalizer`: A utility class to sanitize heading strings (casefold, strip, collapse whitespace).
- `SectionPathBuilder`: Maintains the state of the current section path (traversing `HeadingNode`s) and handles the ordinal tie-breaker logic for sibling collisions.
- Hash functions: `generate_doc_anchor(doc_id)`, `generate_sec_anchor(doc_id, normalized_path)`, `generate_pass_anchor(sec_anchor, block_type, ordinal)`.

---

## 2. Algorithms and Edge Policies

### 2.1 Deterministic Anchor Generation
The anchor generation will use `SHA-256` (hexdigest, defaulting to full 64-char hex to avoid any collision risk). It operates by traversing the hierarchical AST (`DocNode` and `HeadingNode`s) generated in PR3.

1. **Heading Normalization (`normalize_heading`)**:
   - `casefold()` the heading text.
   - Replace any sequence of whitespace characters (including newlines and tabs) with a single space ` " "`.
   - Strip leading and trailing whitespace.

2. **Duplicate Heading Tie-Breaker**:
   - The `SectionPathBuilder` maintains a `Counter` for child `HeadingNode` text at each level under the current parent.
   - When a heading is visited, normalize its text.
   - Check the counter for the parent. If the count is `0`, the path segment is just `normalized_text`.
   - If the count is `> 0`, the path segment becomes `f"{normalized_text}_{count - 1}"` (so the second occurrence is `_0`, the third is `_1`, etc.).
   - Increment the counter.
   - The final `normalized_section_path` is the `>` joined string of these segments.
   - E.g., `H1 > H2_0`.

3. **Anchor Hashes**:
   - `doc_anchor = sha256(doc_id.encode('utf-8')).hexdigest()`
   - `sec_anchor = sha256(f"{doc_id}::{normalized_section_path}".encode('utf-8')).hexdigest()`
     *(Note: we use `::` as a deterministic separator to avoid collision between ID and path).*
   - `pass_anchor = sha256(f"{sec_anchor}::{block_type.value}::{block_ordinal}".encode('utf-8')).hexdigest()`
     *(The `block_ordinal` is a 0-based index of the `BlockNode` under its immediate `HeadingNode` section).*

### 2.2 Range Derivation Logic
Since PR3 builds the AST by tokenizing an existing `canonical_text` string, range derivation operates directly on the indices of that input string, rather than via serialization.

- **Algorithm**:
  - The `RangeTracker` works alongside the `BlockTokenizer` (introduced in PR3) to record exact character indices (`start` and `end`) for every block identified in the `canonical_text`.
  - Empty blocks (if any) receive a zero-length range `[start, start]`.
  - A post-processing validation function `resolve_ranges(tree, canonical_text)` walks the generated AST and asserts the integrity check: `assert 0 <= start <= end <= len(canonical_text)`.
  - It also verifies that slicing `canonical_text[start:end]` accurately captures the node's text.

### 2.3 Malformed Table Fallback Policy
When extracting tables from the `canonical_text` (identified by the tokenizer as contiguous lines starting with `|`):
- A table is considered **malformed** if it lacks a consistent column count (e.g., header row has 2 columns, body rows have 5) and cannot be normalized, or if the parser fails to construct a valid tabular AST node.
- **Fallback**: Instead of dropping the content or failing the pipeline, the parser will extract all text cells from the malformed table, join them with newlines or spaces, and emit a `PARA` `BlockNode`.
- The `metadata` field of the resulting `BlockNode` will be tagged with `{"fallback": "malformed_table"}` to preserve traceability.

---

## 3. Step-by-Step Execution Plan

**Step 1: Implement Anchor Generation (`src/docforge/parsers/anchors.py`)**
- Create `normalize_heading(text: str) -> str`.
- Create `SectionPathBuilder` class to handle AST hierarchy traversal and sibling ordinal logic.
- Implement the SHA-256 hash generation functions: `generate_doc_anchor`, `generate_sec_anchor`, `generate_pass_anchor`.
- *Commit: "feat(parsers): implement deterministic anchor generation and normalization"*

**Step 2: Implement Range Tracking (`src/docforge/parsers/ranges.py`)**
- Create the `RangeTracker` utility to precisely track string indices during tokenization of `canonical_text`.
- Implement `resolve_ranges(...)` which validates a populated AST to ensure accurate `[start, end]` tuples.
- *Commit: "feat(parsers): implement block range derivation logic"*

**Step 3: Integrate Table Fallback Logic**
- Locate the table block logic within `BlockTokenizer`.
- Wrap table structure validation in a try-except/validation block.
- On failure, apply the fallback policy: emit a `PARA` node containing the inner text and the `fallback` metadata tag.
- *Commit: "feat(parsers): add fallback policy for malformed tables"*

**Step 4: Orchestrate in Main Parser Pipeline**
- Wire up `anchors.py` and `ranges.py` inside the parser orchestration layer (e.g., `src/docforge/parsers/tree_builder.py` or the main parse method).
- Ensure the tree correctly populates anchors for all `BlockNode`s and `HeadingNode`s.
- Ensure all nodes get a validated `range`.
- *Commit: "feat(parsers): wire ranges and anchors into main parser pipeline"*

**Step 5: Write and Run Tests**
- Write unit, property, and fixture tests mapping to the required ACs.
- Run `make fmt`, `make lint`, `make type`, `make test`.
- *Commit: "test(parsers): add test suite for PR4 anchor and range policies"*

---

## 4. Test Scenarios Mapping

The following test categories will be added to ensure the implementation fulfills the contract and ACs:

1. **Anchor Determinism & Collisions (`tests/parsers/test_anchors.py`)**
   - *Scenario*: Two identical headings under the same parent (e.g., `# Overview`).
     - *Assert*: First resolves to `overview`, second to `overview_0`. Their `sec_anchor` hashes must differ.
   - *Scenario*: Headings with varying whitespace and casing (`Overview`, `  overview `, `OVERVIEW\n`).
     - *Assert*: All normalize identically to `overview`.
   - *Scenario*: Identical inputs parsed twice.
     - *Assert*: All generated hashes are strictly identical across runs.

2. **Range Resolvability (`tests/parsers/test_ranges.py`)**
   - *Scenario*: Generate ranges for a document with mixed paragraphs, code blocks, and empty blocks.
     - *Assert* (Property Test): For every block `i`, `0 <= start_i <= end_i <= len(canonical_text)`.
     - *Assert*: Slicing `canonical_text[start:end]` exactly yields the block's text content.
   - *Scenario*: Zero-length block.
     - *Assert*: Range is `[offset, offset]` and slice returns `""`.

3. **Malformed Table Fallback (`tests/parsers/test_edge_policies.py`)**
   - *Scenario*: Provide a broken markdown table (e.g., mismatched column counts) in `canonical_text`.
     - *Assert*: Parser does not crash.
     - *Assert*: Emitted tree contains a `BlockNode` of type `PARA` containing the extracted text.
     - *Assert*: Block metadata contains `{"fallback": "malformed_table"}`.