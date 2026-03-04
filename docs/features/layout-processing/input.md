dockling link: https://huggingface.co/ibm-granite/granite-docling-258M

what to consider:
- unstructured
- IBM dockling

# analysis-1:
You can treat your JSON “blocks with positions” as a layout graph problem: normalize geometry, merge into lines/paragraphs/columns, then promote those groups into a document tree (sections, tables, figures) and finally run semantic enrichment (embeddings/NER/LLM). If you’d rather not build that yourself, there are higher-level libraries that already output typed “elements” or full document hierarchies you can align your blocks to.

## Geometry-first merging
Start by defining a canonical schema for every block: `(page, bbox in a single coordinate system, text, optional font/style, source, confidence)` plus derived features like `x_center, y_center, height, width`. Then merge in stages: characters→words (if needed), words→lines (same baseline / y-overlap), lines→paragraphs (vertical gap + indentation), paragraphs→columns (cluster by x bands) and pages→reading order (per column, then across columns).

Implementation-wise, the most reliable approach is: spatial indexing (R-tree), “nearby” candidate generation, then deterministic merge rules + a small number of learned heuristics you can tune on your corpus (e.g., hyphenation repair, header/footer detection, repeated boilerplate removal).

## Layout-aware assembly options
If you want ML-assisted region detection (titles, text, tables, figures) and then map your blocks into those regions, LayoutParser is a common choice: it provides APIs around deep-learning layout detection to extract complicated document structures without hand-written rule systems. [github](https://github.com/Layout-Parser/layout-parser)

If you want a ready-made “elements” abstraction (Title, NarrativeText, Table, etc.) and configurable strategies, Unstructured’s `partition_pdf` segments PDFs using document image analysis and exposes strategies like `fast`, `hi_res`, and `ocr_only` (with notes about multi-column ordering challenges in `hi_res`).  In practice, you can either (a) replace your pipeline with Unstructured, or (b) use it as a second pass to *label* your existing blocks and then merge within each label. [layout-parser.github](https://layout-parser.github.io)

If you want a full structured hierarchy and explicit relationships like reading order / hierarchy / caption↔figure links, IBM’s Docling/Granite-Docling ecosystem centers on DocTags, which is designed to capture page elements *and* their relations and can be converted to Markdown/JSON/HTML (or fed into Docling pipelines). [arxiv](https://arxiv.org/abs/2103.15348)

## Semantic assembling (after layout)
Once you have stable “chunks” (paragraphs/sections/table objects) with provenance metadata, semantic work gets much easier:
- Build a section tree: detect headings (font/size if available; otherwise regex + spacing cues) and attach subsequent paragraphs until the next heading.
- Classify chunk types (definition, procedure, requirement, disclaimer) using a lightweight classifier or an LLM, then store as tags for retrieval/routing.
- Do entity and citation linking: normalize entities, attach them to chunks, and optionally create a doc-level knowledge graph (entities ↔ sections ↔ tables).

For RAG, prefer “structure-preserving chunks”: store section path, page range, bbox union, and (for tables) HTML/CSV + a textual summary, rather than flattening everything into plain text.

## A pragmatic architecture
A robust pattern is a 3-layer pipeline:
1) **Layout layer**: your corrected blocks + normalization + merge to lines/paragraphs/columns (deterministic, debuggable).
2) Structure layer: optional LayoutParser/Unstructured/Docling alignment to label regions or build a hierarchy. [github](https://github.com/Layout-Parser/layout-parser)
3) Semantics layer: chunking-by-section, embeddings, NER, LLM transforms, quality checks (e.g., “no chunk crosses columns”, “table has rectangular cell grid”, “reading order monotonic within a column”).

What target artifact do you ultimately want to produce from the assembled blocks (Markdown/HTML, a “document tree” JSON schema, or RAG-ready chunks)?

# markdown additions

Build a “lossless” document tree JSON that stores structure + provenance to your original blocks, then generate Markdown views from that tree using stable node IDs and explicit mappings (node↔markdown file↔text spans). If you get the JSON/Markdown contract right up front, embeddings/RAG become a straightforward enrichment step instead of a re-chunking fight later.

## Target outputs
Aim for two synchronized artifacts:
- `document.json`: canonical truth (tree, types, provenance, reading order, relationships).
- `md/…/*.md`: render-oriented views (easy diffing, human QA, downstream LLM transforms) that still point back to JSON nodes.

If you want a reference design, Docling explicitly supports exporting a unified “Docling Document” to **Markdown** and a lossless **JSON** serialization, plus DocTags for representing content and layout characteristics. [youtube](https://www.youtube.com/watch?v=wyOcemlHq_o)

## Document tree JSON (practical schema)
Keep the schema small but expressive; you can always extend via `meta`.

Recommended top-level shape:
- `doc`: `{doc_id, source_uri, created_at, version, meta}`
- `pages[]`: `{page_no, width, height, rotation, blocks_ref[]}` (optional but helps debugging)
- `nodes{node_id -> node}`: normalized node store
- `root_id`: points at the root node

Node shape (works well for RAG + traceability):
- `node_id`: stable, deterministic if possible (hash of normalized text + provenance ids)
- `type`: `document|section|paragraph|list|list_item|table|figure|caption|code|equation|header|footer`
- `parent_id`, `children[]`
- `text`: plain text (for semantic indexing); keep it empty for tables/figures if you store them separately
- `markdown_ref`: `{path, anchor}` (optional, see next section)
- `provenance[]`: list of source spans, each like:
  - `{page_no, bbox, source_block_ids[], reading_order_hint, confidence}`
- `layout`: `{bbox_union, column_id, line_ids[]}` (optional but extremely useful)
- `meta`: `{heading_level, font_stats, detected_lang, tags[], …}`

Two “make it future-proof” rules:
- Never rely on Markdown as ground truth; it’s just a projection.
- Store *relationships explicitly* (e.g., `caption_of: figure_node_id`, `table_mentions: [node_ids]`, `footnote_refs`, etc.).

## Parallel Markdown (without losing alignment)
A clean pattern is “one Markdown file per top-level section (or per page), plus stable anchors per node”.

Example conventions:
- File granularity:
  - `md/section_{node_id}.md` for each `section` node, or
  - `md/page_{page_no}.md` if your PDFs are very layout-driven.
- Inside Markdown, add lightweight anchors so you can round-trip:
  - HTML comments: `<!-- node:abc123 -->`
  - Or heading anchors: `## Title {#node-abc123}` (depending on your renderer)

Mapping strategy (robust for later augmentation):
- In `document.json`, store `markdown_ref.path` for each node plus `char_span` offsets into that file (if you need exact alignment for highlights).
- For offsets, compute spans from the generated Markdown string (don’t try to infer them after the fact).

For tables:
- Store a structured table object in JSON (`cells`, `row/col spans`, `bbox`, `caption_id`).
- Render Markdown as:
  - a normal Markdown table when it’s small and rectangular, or
  - a link to an adjacent artifact like `tables/{table_id}.html` / `tables/{table_id}.csv` if fidelity matters.

## Assembly pipeline (blocks → tree)
Given you already have corrected blocks w/ positions, a deterministic 6-stage pipeline is usually enough:

1) Normalize coordinates: one coordinate system, consistent page origin, bbox sanity checks.  
2) Merge to lines: y-overlap/baseline heuristics + whitespace inference.  
3) Merge to paragraphs: vertical gap + indentation + punctuation/hyphenation rules.  
4) Column + reading order: cluster by x-bands (per page), then top-to-bottom within a column, then left-to-right across columns.  
5) Promote structure: heading detection (style if available; otherwise regex + spacing cues), build a section stack, attach following nodes until next heading.  
6) Attach non-text objects: tables/figures/captions, link by spatial proximity + “caption-like” text patterns.

If you also run Unstructured as a labeling pass, its elements can carry coordinates in `element.metadata.coordinates` (bbox points + coordinate system details), which can help you validate your geometry normalization and region typing. [unstructured.readthedocs](https://unstructured.readthedocs.io/en/main/metadata.html)

## Libraries & building blocks
For a custom pipeline (fast iteration, debuggable):
- Schema + validation: `pydantic` (models), `jsonschema` (exported validation), `orjson` (fast IO).
- Geometry + indexing: `shapely` (bbox unions/intersections), `rtree` (spatial neighbor queries), `numpy` (vectorized features).
- Tree/graph ops: `networkx` (when you start adding cross-links beyond parent/child).
- Text cleanup: `regex`, `ftfy` (unicode fixes), `rapidfuzz` (detect repeated headers/footers / near-duplicates).

If you’d prefer an off-the-shelf “tree + exporters” approach, Docling’s `DoclingDocument` model is explicitly a tree of typed items and includes export methods like `export_to_markdown` and lossless JSON serialization. [labelstud](https://labelstud.io/videos/customized-layout-detection-for-scientific-pdfs-with-layoutparser-and-label-studio/)

Do you want the Markdown files split **per section** or **per page**?  
