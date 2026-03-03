# User Stories: Structural Parser & Distiller

## 1. Personas and Outcomes
- As a pipeline operator, I need parser output to be stable and measurable so ingest runs are reproducible.
- As a downstream segmenter developer, I need structural boundaries and valid ranges so segmentation logic can consume parser output without ad hoc cleanup.
- As a retrieval/citation consumer, I need anchors that resolve deterministically to source-derived text.

## 2. Acceptance Criteria

### AC1: Canonical UTF-8 output
- Given a `RawDocument` containing parseable textual content
- When the document is processed by the parser
- Then `canonical_text` is valid UTF-8 text
- And `canonical_text` is non-empty

### AC2: Heading hierarchy integrity
- Given a document containing heading levels (for example H1/H2/H3)
- When `structure_tree` is produced
- Then heading parent-child relationships are preserved in document order
- And non-heading blocks are attached to exactly one parent node

### AC3: Table preservation
- Given a document containing a table
- When the parser emits `canonical_text` and `structure_tree`
- Then a `table` block exists in `structure_tree`
- And table header semantics are preserved in canonical representation

### AC4: Code block preservation
- Given a document containing fenced code blocks
- When the parser emits `canonical_text` and `structure_tree`
- Then a `code` block exists in `structure_tree`
- And code content whitespace/indentation is preserved verbatim (aside from newline normalization policy)
- And language metadata is captured when present

### AC5: Deterministic anchors
- Given the same document bytes, parser version, and parser config
- When parsing is executed repeatedly
- Then `doc_anchor`, `sec_anchor`, and `pass_anchor` values are identical across runs

### AC6: Range resolvability
- Given any block node with `range = [start, end]`
- When `canonical_text[start:end]` is extracted
- Then the extracted substring equals that block's canonical content

### AC7: Duplicate heading tie-breaker
- Given sibling headings that normalize to the same path
- When section anchors are generated
- Then deterministic ordinal tie-breakers are applied
- And each resulting `sec_anchor` is unique within the document

## 3. Failure and Edge Scenarios

### ES1: Malformed table fallback
- Given malformed table content that cannot be reliably parsed as table structure
- When parsing runs
- Then parser must preserve recoverable text content
- And output remains valid without crashing

### ES2: Skipped heading levels
- Given a heading jump (for example H1 directly to H3)
- When `structure_tree` is built
- Then tree remains valid and acyclic
- And synthetic intermediate headings are not required

### ES3: Content without headings
- Given a document with paragraphs/lists but no headings
- When parsing runs
- Then blocks are attached to document root
- And anchor/range generation remains valid

### ES4: Empty or near-empty content
- Given empty bytes or bytes that normalize to no textual content
- When parsing runs
- Then output is well-formed and deterministic
- And no unhandled exception is raised

## 4. Traceability Matrix
| ID | RFC reference | Test category |
|---|---|---|
| AC1 | [01_rfc.md §2.3, §5](./01_rfc.md) | Unit + corpus quality check |
| AC2 | [01_rfc.md §2.2, §3.1, §3.2](./01_rfc.md) | Property |
| AC3 | [01_rfc.md §1, §3.1, §5](./01_rfc.md) | Unit |
| AC4 | [01_rfc.md §1, §3.1, §5](./01_rfc.md) | Unit |
| AC5 | [01_rfc.md §3.1, §4](./01_rfc.md) | Snapshot + property |
| AC6 | [01_rfc.md §2.3, §3.1](./01_rfc.md) | Property |
| AC7 | [01_rfc.md §3.2, §4.1](./01_rfc.md) | Unit + property |
| ES1 | [01_rfc.md §3.1, §5](./01_rfc.md) | Unit |
| ES2 | [01_rfc.md §3.1, §3.2](./01_rfc.md) | Property |
| ES3 | [01_rfc.md §2.2, §3.1](./01_rfc.md) | Unit |
| ES4 | [01_rfc.md §3.1, §5](./01_rfc.md) | Unit |

## 5. Quality Gates
- >= 99% of parser-eligible corpus documents produce non-empty `canonical_text`.
- 100% of emitted blocks have valid `range` values resolvable in `canonical_text`.
- Re-run determinism checks pass for golden corpus snapshots.
- Table and code preservation checks pass on dedicated fixtures.
