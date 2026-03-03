# User Stories: Structural Parsers

## 1. Personas and Outcomes
- **Platform engineer**: needs deterministic parser outputs to avoid index churn.
- **RAG engineer**: needs anchorable segments for precise citations.
- **ML engineer**: needs stable section/passage contracts for augmentor and embeddings.
- **SRE/owner**: needs explicit failure modes for unsupported formats and parse errors.

## 2. Acceptance Criteria
### AC1: Deterministic canonicalization
- Given the same `RawDocument` bytes and parser config
- When canonicalization runs repeatedly
- Then `canonical_text` is byte-identical
- And extracted structure ordering is unchanged

### AC2: Anchorability and uniqueness
- Given a parsed document with repeated heading names
- When anchors are generated
- Then each section/block anchor is unique in document scope
- And each anchor resolves back to source context

### AC3: Hierarchical segmentation integrity
- Given a document with nested headings
- When sections/passages are created
- Then parent-child pointers form an acyclic hierarchy
- And every `PASSAGE` has a valid `SECTION` ancestor

### AC4: Table and code preservation
- Given documents containing tables and code blocks
- When segmentation occurs
- Then table headers and code boundaries are preserved
- And split behavior follows configured fallback policy for oversized blocks

### AC5: Explicit failure behavior
- Given unsupported or invalid content payloads
- When parser execution runs
- Then typed errors are emitted with doc context
- And no partial malformed artifacts are published as successful output

## 3. Failure and Edge Scenarios
### ES1: Empty body document
- Given empty content bytes after decoding
- When parsing runs
- Then parser returns a valid empty/minimal structure with doc anchor
- And emits zero passages (or one empty passage per RFC decision)

### ES2: Heading collision storm
- Given many identical headings in one document
- When section anchors are generated
- Then deterministic suffixing prevents collisions
- And stable order is maintained

### ES3: Oversized monolithic code block
- Given one code block exceeding max passage budget
- When segmenting
- Then parser splits at logical boundaries when available
- And preserves language metadata and context continuity

## 4. Traceability Matrix
| ID | RFC reference | Test category |
|---|---|---|
| AC1 | `01_rfc.md §3.1(1), §3.2` | Unit + fixture determinism |
| AC2 | `01_rfc.md §3.1(2), §4` | Unit/property |
| AC3 | `01_rfc.md §3.1(3)` | Unit/integration |
| AC4 | `01_rfc.md §2.2, §5` | Fixture + integration |
| AC5 | `01_rfc.md §2.3, §5` | Unit/integration |
| ES1 | `01_rfc.md §2.2` | Unit |
| ES2 | `01_rfc.md §4` | Unit/property |
| ES3 | `01_rfc.md §3.1(4), §5` | Fixture/integration |

## 5. Quality Gates
- All AC rows mapped to automated tests before parser feature is marked done.
- Determinism checks must execute at least two runs over fixed fixtures.
- Contract/schema checks block merge on failures.
