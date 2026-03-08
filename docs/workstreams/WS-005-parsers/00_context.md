# Context: Structural Parser & Distiller

## 1. Purpose in Pipeline
The Structural Parser & Distiller (component 3.2 in `docs/mvp-1.md`) transforms source-specific raw documents into canonical, structured text with stable anchors.

- Upstream: Source Connectors (component 3.1).
- Downstream: Hierarchical Segmenter (component 3.3).
- Module path: `src/docforge/parsers/`.

## 2. Component Boundaries
### Owns
- Canonicalization into UTF-8 `canonical_text`.
- Extraction of heading/block hierarchy in `structure_tree`.
- Generation of deterministic `doc_anchor`, `sec_anchor`, and `pass_anchor`.
- Character-range resolvability of block nodes.

### Does Not Own
- Source fetch/enumeration and sync state.
- Passage token sizing/chunking policy.
- LLM augmentation or graph extraction.

## 3. Upstream/Downstream Contracts
- Input contract (`RawDocument`) and output contract (`ParsedDocument`) are defined normatively in [01_rfc.md](./01_rfc.md).
- This context document is non-normative and must not redefine schema details.

## 4. Invariants Summary
- Determinism: same bytes + same parser version/config => same output.
- Anchorability: each anchor resolves to section path or canonical range.
- Hierarchical integrity: parsed tree is acyclic and structurally valid.
- Information preservation: code remains verbatim; table headers remain represented.

## 5. Golden Example (Compact)
Input markdown:
~~~markdown
# My Project
Here is a description.
## Setup
```python
print("hello")
```
~~~

Expected outcomes:
- `canonical_text` contains both headings, paragraph text, and code block text.
- `structure_tree` captures `H1 -> H2` relationship, with paragraph and code blocks attached in order.
- Anchors include one `doc_anchor`, section `sec_anchor` values for `My Project` and `My Project>Setup`, and block-level `pass_anchor` values with valid ranges.

## 6. Verification Map
| Contract area | Verification family | Example checks |
|---|---|---|
| Determinism | Snapshot/property | Same input twice yields byte-identical parser output |
| Anchorability | Property | Every `pass_anchor` maps to valid `canonical_text[range[0]:range[1]]` |
| Hierarchical integrity | Property | Acyclic tree, valid parent-child heading nesting |
| Table/code fidelity | Unit | Header-preserving table output; verbatim code whitespace |
