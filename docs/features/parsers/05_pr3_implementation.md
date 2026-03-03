# PR3 Implementation Plan: Structure Tree Extraction

This document outlines the implementation plan for PR3, satisfying the scope defined in the Workplan (`docs/features/parsers/04_workplan.md`) to parse the canonical text and build a deterministic `structure_tree`.

## 1. Architectural Breakdown

PR3 introduces the logic required to parse the `canonical_text` generated in PR2 into a strict, validated hierarchical AST defined in `models.py`.

### `src/docforge/parsers/tree_builder.py`
**Responsibility:** Tokenize the `canonical_text` into blocks and arrange them into the valid acyclic hierarchy represented by `DocNode`, `HeadingNode`, and `BlockNode`.
**Key Components:**
- `BlockTokenizer`: A utility that iterates over the `canonical_text` string to yield intermediate token objects (identifying `PARA`, `LIST`, `TABLE`, `CODE`, or `HEADING` with its level and text).
- `build_tree(canonical_text: str) -> DocNode`: Consumes tokens, builds the hierarchy using a heading-aware stack, and populates preliminary byte/character ranges.

## 2. Algorithms and Edge Policies

### 2.1 Block Tokenization
The `canonical_text` produced by PR2 is a predictably formatted markdown-like string. The tokenizer will operate by traversing lines and identifying block boundaries:
- **Code Blocks**: Fenced by ` ``` `. Content and newlines within the fence belong to the `CODE` block.
- **Tables**: Contiguous lines starting with `|`.
- **Lists**: Contiguous lines starting with `- ` or matching `\d+\. ` (unordered or ordered).
- **Headings**: Lines matching `^(#{1,6})\s+(.+)$`.
- **Paragraphs**: Contiguous lines of text not matching the above, typically separated by blank lines.

*Note on ranges:* The tokenizer will track `start` and `end` offsets in the `canonical_text` string using Python's string slicing or line length tracking. While PR4 will formalize range derivation and strict policies, PR3 will pre-fill valid `range` attributes so `BlockNode` validation passes seamlessly.

### 2.2 Heading Stack Algorithm
1. Initialize `stack = [DocNode(children=[])]`.
2. For each tokenized block:
   - **If Heading**:
     - Extract `level` (1-6).
     - `while len(stack) > 1` and the top of the stack is a `HeadingNode` with `level >= current_level`:
       - `stack.pop()`
     - Create `HeadingNode(level=current_level, text=..., children=[])`.
     - Append to `stack[-1].children`.
     - Push the new `HeadingNode` onto `stack`.
   - **If Non-Heading (Block)**:
     - Create `BlockNode(type=..., range=(start, end), metadata=...)`.
     - Append to `stack[-1].children`.
3. Return `stack[0]` (the root `DocNode`).

### 2.3 Edge-Case Handling
- **Missing Headings**: If the document starts with paragraphs before any heading, the `stack` length is 1 (`DocNode`), and blocks attach directly to the root fallback path.
- **Skipped Heading Levels**: If an H1 is followed immediately by an H3, the `while` loop condition safely pops until it finds the H1, attaching the H3 directly to the H1. The tree remains valid and acyclic without synthesizing missing levels.
- **Empty Docs**: An empty `canonical_text` bypasses the loop and returns a `DocNode` with zero children.

## 3. Step-by-Step Execution Plan

**Step 1: Intermediate Tokenizer**
- Implement `BlockTokenizer` (or equivalent simple tokenization function) in `tree_builder.py`.
- Ensure it successfully distinguishes between `PARA`, `LIST`, `TABLE`, `CODE`, and headings, capturing raw offsets.
- *Commit: "feat(parsers): implement tokenizer for canonical text blocks"*

**Step 2: Tree Construction Logic**
- Implement `build_tree(canonical_text: str) -> DocNode`.
- Apply the stack-based attachment algorithm.
- *Commit: "feat(parsers): implement deterministic tree builder and heading stack"*

**Step 3: Parser Integration**
- Update `src/docforge/parsers/default.py` to use `build_tree` to populate the `structure_tree` field, replacing the currently hardcoded empty `DocNode`.
- *Commit: "feat(parsers): integrate tree extraction into default parser"*

**Step 4: Tests**
- Write property tests ensuring the tree is acyclic and heading nesting is valid (`test_tree_builder.py`).
- Write fixture tests covering edge cases (skipped heading levels, heading-free docs, empty docs).
- Run the required command sequence (`make fmt`, `make lint`, `make type`, `make test`).
- *Commit: "test(parsers): add property and edge-case tests for tree building"*

## 4. Test Scenarios Mapping
1. **Hierarchy Integrity**
   - *Scenario*: Parse text with H1 -> H2 -> H3 -> H2.
     - *Assert*: The second H2 is a sibling of the first H2, both children of H1.
   - *Scenario*: Document without headings.
     - *Assert*: All `BlockNode`s are direct children of the `DocNode`.
2. **Skipped Levels**
   - *Scenario*: H1 followed by H4.
     - *Assert*: H4 is a direct child of H1.
3. **Block Types**
   - *Scenario*: Mixed document with tables, code fences, lists, and paragraphs.
     - *Assert*: Tree contains exactly the expected count of each `ParserBlockType`.