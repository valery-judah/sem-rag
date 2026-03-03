# Context: Parsers

## Purpose in Pipeline
- Component: Structural Parser & Distiller (Phase 1 component 3.2)
- Module path: `src/docforge/parsers/`
- Upstream dependency: source connectors (`RawDocument` producers)
- Downstream dependency: hierarchical segmenter (`ParsedDocument` consumers)

## Component Boundaries
### Owns
- Canonicalization into UTF-8 `canonical_text`
- `structure_tree` extraction
- deterministic anchor generation (`doc_anchor`, `sec_anchor`, `pass_anchor`)
- range/offset resolvability

### Does Not Own
- Source fetch/list/cursor logic
- Segmentation/token policy
- LLM augmentation and graph extraction

## Contract References
- Normative contracts for this feature:
  - [Parsers RFC (canonical)](/Users/val/projects/rag/sem-rag/docs/parsers/01_rfc.md)
  - [Agentic RFC mirror/local](/Users/val/projects/rag/sem-rag/docs/features/parsers/01_rfc.md)

## Invariants Summary
- Determinism for fixed bytes + parser version/config
- Anchorability from every block/section anchor to canonical representation
- Hierarchical integrity (acyclic + valid parentage)
- Table/code preservation semantics

## Golden Example (Compact)
Input:
~~~markdown
# My Project
Some text
## Setup
```python
print("hello")
```
~~~

Expected outcomes:
- `canonical_text` is non-empty UTF-8
- `structure_tree` contains `H1 -> H2` plus paragraph/code blocks
- section and block anchors are deterministic and resolvable

## Verification Map
| Contract area | Verification family | Example checks |
|---|---|---|
| Determinism | Snapshot/property | Reparse same input yields identical output |
| Anchorability | Property | `canonical_text[range[0]:range[1]]` matches block text |
| Hierarchical integrity | Property | Acyclic tree, valid parent attachment |
| Table/code fidelity | Unit | Header-preserving table and verbatim code checks |
