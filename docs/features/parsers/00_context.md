# Context: Structural Parsers

## Purpose in Pipeline
- Component: Structural Parser & Distiller + Hierarchical Segmenter
- Module path: `src/docforge/parsers/` (planned)
- Upstream dependency: connector outputs (`RawDocument` from Phase 1 connectors)
- Downstream dependency: augmentor, embedding/index publishing, graph extraction

## Component Boundaries
### Owns
- Format-to-canonical-text conversion (UTF-8 normalized)
- Structure tree extraction (headings/lists/tables/code/paragraph blocks)
- Anchor production (`doc`, `section`, `block/passage`)
- Section/passage segmentation with deterministic IDs

### Does Not Own
- Source fetching and connector incrementality
- LLM augmentation prompt quality/policies
- Index serving and retrieval orchestration
- Runtime retries/scheduling/deployment

## Contract References
- Normative contracts: `./01_rfc.md`
- Phase baseline: `docs/phase-1.md` §2, §3.2, §3.3

## Invariants Summary
- Stable identity for unchanged input/config/doc version
- Every segment and derivative references resolvable anchors
- Parent-child hierarchy is acyclic and valid
- Repeat runs with identical inputs produce equivalent outputs

## Golden Example (Compact)
Input:
```text
# Payments
## Retry Policy
If the charge fails...
```

Expected outcomes:
- `doc_anchor` exists and resolves to source doc
- `section` nodes for `Payments` and `Payments>Retry Policy`
- one or more `PASSAGE` segments with stable `segment_id` and `anchor`
- segment lineage can be traced to section and document anchors

## Verification Map
| Contract area | Verification family | Example checks |
|---|---|---|
| Canonicalization determinism | Unit + fixture | repeated parse byte-equality |
| Anchor policy | Unit/property | uniqueness + collision suffixing |
| Hierarchy integrity | Unit/integration | no cycles, parent IDs valid |
| Segmentation policy | Unit/integration | token bounds + table/code handling |
