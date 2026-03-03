# Workplan: Structural Parser & Distiller

## PR1: Scaffolding + Schema
- [ ] Define `RawDocument` and `ParsedDocument` Pydantic models (or dataclasses).
- [ ] Define the `structure_tree` node types (Doc, Heading, Para, Table, Code, List).
- [ ] Implement the base `Parser` interface.
- [ ] Add empty configuration schema for `parsing`.
- [ ] **Tests:** Unit tests validating Pydantic model serialization/deserialization.
- [ ] **Docs updates:** Update API docs if necessary.

## PR2: Text Canonicalization
- [ ] Implement `HtmlToMarkdownConverter` (using BeautifulSoup + Markdownify or similar).
- [ ] Implement whitespace and newline normalization logic (excluding code blocks).
- [ ] Integrate converter into the main `Parser.parse()` flow based on `content_type`.
- [ ] **Tests:** Unit tests covering HTML to Markdown conversion, plain text handling, and whitespace normalization.

## PR3: Structure Tree Extraction
- [ ] Implement Markdown AST parsing (using `mistune` or similar).
- [ ] Implement the stack-based tree building algorithm to extract heading hierarchies.
- [ ] Handle attachment of standard blocks (paragraphs, lists) to the correct heading parent.
- [ ] Implement edge-case logic for missing or skipped heading levels.
- [ ] **Tests:** Structural property tests (acyclic, single parent, correct level nesting).

## PR4: Special Blocks + Offsets + Anchors
- [ ] Implement specialized extraction for `table` blocks (preserving headers).
- [ ] Implement specialized extraction for `code` blocks (preserving verbatim whitespace and extracting language tags).
- [ ] Implement the character offset calculation logic, assigning `range` to all block nodes.
- [ ] Implement the deterministic anchor generation strategy (hashing paths + ordinals).
- [ ] **Tests:** Unit tests for table/code extraction, property tests for anchor stability, and exact character range extraction tests.

## PR5: Determinism Snapshots + Observability
- [ ] Wire up observability events (`DocParsed`, `PipelineError`).
- [ ] Create a representative golden corpus (HTML, Markdown, Plain Text).
- [ ] Implement snapshot tests for the golden corpus to enforce determinism and protect against silent regressions.
- [ ] Generate a pipeline quality report outlining success rates and node distributions.
- [ ] **Tests:** CI gates for determinism snapshot mismatches.
