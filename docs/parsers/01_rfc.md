# RFC: Structural Parser & Distiller

## 1. Problem Statement
Raw documents ingested from corporate sources (Confluence, Jira, Google Drive, Git repositories) come in a myriad of formats (HTML, Markdown, Plain Text). Attempting to chunk and index these raw formats directly leads to poor retrieval quality because structure (headings, tables, code blocks) is often destroyed or obfuscated. 

We need a unified **Structural Parser & Distiller** to convert raw documents into a canonical, cleanly-structured text representation (typically normalized Markdown-like structure) while explicitly extracting the hierarchical tree (headings) and preserving semantic units (tables with headers, verbatim code blocks). This component must also establish stable anchors to enable precise citation and provenance tracking down the line.

## 2. Scope
### In Scope
- Conversion of HTML, Markdown, and Plain Text into canonical UTF-8 text.
- Extraction of heading hierarchies to build a document structure tree.
- Identification and specialized parsing of structural blocks:
  - **Tables:** Converting to a format that retains row/col headers (e.g., Markdown tables).
  - **Code blocks:** Extracting language tags and preserving exact whitespace/newlines.
  - **Lists:** Normalizing list structures.
- Generation of stable anchors: `doc_anchor`, `sec_anchor` (section level), and `pass_anchor` (block/passage level).
- Calculating exact character offset ranges for all blocks within the canonical text.

### Out of Scope
- Fetching documents from APIs (handled by Connectors).
- Segmenting or chunking text into token-limited passages (handled by Hierarchical Segmenter).
- OCR or image transcription (PDFs will only use text-layer extraction in Phase 1 if supported, otherwise deferred).
- LLM-based parsing or extraction (parsing must be fast, deterministic, and algorithmic).

## 3. Success Criteria
- **Robustness:** $\ge 99\%$ of ingested documents produce a non-empty `canonical_text` and a valid structure tree without raising unhandled exceptions.
- **Structural Integrity:** Heading hierarchy is correctly extracted wherever present in the source HTML/Markdown.
- **Fidelity:** Tables and code blocks are explicitly tagged in the structure tree, with contents preserved.
- **Determinism:** Re-parsing the same document yields the exact same canonical text and anchor hashes.

## 4. Open Decisions
1. **HTML Parsing Engine:** Which library to use for HTML to Markdown/canonical conversion? 
   *Proposal:* Use a robust parser like `BeautifulSoup` paired with `markdownify` or build a lightweight custom AST traverser for precise control over table and code extraction.
2. **Anchor Hashing Strategy:** How do we compute stable section anchors?
   *Proposal:* Hash a combination of the `doc_id` + the normalized heading path (e.g., `SHA256(doc_123 + "H1>H2")`). For blocks, append the block's ordinal index within the section.

## 5. Rollout Strategy
The parser will be integrated directly into the ingestion pipeline. 
1. **Local Corpus Testing:** Run parser across a diverse golden corpus of 500 documents (mixing Confluence HTML, Git Markdown, Jira descriptions) and manually verify structural outputs.
2. **Snapshot Enforcement:** Commit snapshot tests for a representative subset of documents to prevent silent regressions during future parser tuning.
3. **Pipeline Integration:** Wire up between Connectors and the Segmenter. Monitor the `PipelineError` observability events and the $\ge 99\%$ success rate KPI during the initial corpus ingestion.
