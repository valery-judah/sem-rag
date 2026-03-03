# Design: Structural Parser & Distiller

## Frozen Contract

### Inputs
- **`RawDocument`**: `doc_id` (string), `content_bytes` (bytes), `content_type` (enum/string), `source` (string), `metadata` (dict).

### Outputs
- **`ParsedDocument`**:
  - `doc_id`: Originating document identifier.
  - `title`: Extracted or provided document title.
  - `canonical_text`: The fully normalized, UTF-8 string representation of the document.
  - `structure_tree`: A hierarchical JSON representation of the document's headings and structural blocks.
  - `anchors`: A dictionary containing `doc`, `sections`, and `blocks` mapping structure to stable hashes and text ranges.
  - `metadata`: Original metadata passed through, potentially augmented with parser-specific flags (e.g., `parser_version`).

### Required Fields
- `canonical_text` must be a non-empty string if the source has textual content.
- `structure_tree` must have a root node of type `doc`.
- Every leaf node in `structure_tree` must have a valid `range` array `[start_char_index, end_char_index]`.

### Invariants
- **Determinism:** `hash(parse(doc_A)) == hash(parse(doc_A))` must hold true across executions.
- **Anchorability:** Every section and block must receive a deterministically generated, stable anchor hash.
- **Hierarchical Integrity:** The tree must be acyclic. Every block belongs to exactly one parent (the preceding heading or the document root).

### Deterministic Ordering Rules
- **Sections:** Ordered strictly by their appearance in the source document (top-to-bottom traversal).
- **Blocks:** Ordered strictly by their appearance within their parent section.
- **Tie-breakers:** For anchors with identical structural paths (e.g., two identical H2s), append a sequential ordinal (`_1`, `_2`) based on document order.

### ID / Anchor Strategy
- `doc_anchor`: `hash(doc_id + version_hash)`
- `sec_anchor`: `hash(doc_id + version_hash + normalized_heading_path + [ordinal if duplicate])`
- `block_anchor`: `hash(sec_anchor + block_type + ordinal_within_section)`

### Config Schema & Defaults
```yaml
parsing:
  preserve_tables: true
  preserve_code_blocks: true
  html_to_markdown: true # Normalize HTML inputs to Markdown syntax internally
```

## Algorithm Overview
1. **Canonicalization:** Inspect `content_type`. If HTML, pass through an HTML-to-Markdown converter. If plain text, wrap in standard paragraphs. If Markdown, use as-is.
2. **AST Parsing:** Parse the canonical Markdown text into an Abstract Syntax Tree (AST) using a robust library (e.g., `mistune` or `markdown-it-py`).
3. **Tree Building (Heading Hierarchy):**
   - Initialize a stack with the root `doc` node.
   - Iterate through AST nodes sequentially.
   - If node is a heading: Pop from the stack until the top node has a lower heading level (e.g., H1 is lower number than H2). Push the new heading node onto the stack.
   - If node is a block (paragraph, list, table, code): Attach it as a child to the node currently at the top of the stack.
4. **Offset Calculation:** Traverse the generated structure tree while tracking character positions in the `canonical_text` to assign precise `[start, end]` ranges to every block node.
5. **Anchor Assignment:** Perform a final pass over the structure tree to generate and assign `doc`, `sec`, and `pass` (block) anchors using the deterministic ID strategy.

## Edge-Case Policy
- **Missing Headings:** If a document starts with blocks before any heading is defined, attach those blocks directly to the root `doc` node.
- **Skipped Heading Levels:** If a document jumps from H1 to H3, treat the H3 as a direct child of the H1. Do not synthesize fake H2s.
- **Malformed Tables:** If an HTML/Markdown table cannot be parsed properly (e.g., missing columns), fall back to treating its contents as standard paragraph text, preserving as much raw string data as possible.
- **Nested Code Blocks:** Standardize to the outermost code block fence. Inner fences are treated as verbatim string content.
- **Empty Documents:** Return a `ParsedDocument` with an empty `canonical_text`, an empty structure tree (only the root node), and a single `doc_anchor`.

## Decisions & Tie-breakers
- **Decision 1 (Canonical Format):** We will normalize all documents to a Markdown-like canonical text format internally before building the structure tree. This unifies the logic for handling both Confluence HTML and native Git Markdown.
- **Decision 2 (Whitespace):** Multiple consecutive blank lines outside of code blocks will be normalized to a single blank line to ensure cleaner character offsets and chunking downstream.
- **Tie-breaker (Duplicate Headings):** If a document has two `## Setup` sections under the same H1, their paths will be `H1>Setup_0` and `H1>Setup_1` respectively to maintain stable, unique anchors.
