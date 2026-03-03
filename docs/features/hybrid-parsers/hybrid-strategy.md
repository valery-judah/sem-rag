# Hybrid PDF Parsing Strategy: Marker vs. MinerU

## Overview
This document outlines a strategy for handling complex PDF parsing by intelligently combining multiple parsing engines—primarily **Marker**, **MinerU**, and **PyMuPDF**. Rather than forcing a global choice between layout-heavy models (Marker/MinerU) and geometry-based models (PyMuPDF), this strategy advocates for a **Hybrid Routing Strategy** that evaluates and processes documents on a per-page basis.

## Analysis of Marker and MinerU

Based on an analysis of parsing artifacts (specifically smoke tests run against `llm-evals-course-notes-july.pdf`):

### Marker
* **Strengths:** Excellent at preserving text formatting (italics, bold) and explicitly tagging markdown headings (e.g., `#`, `##`). It also does a decent job keeping tables of contents aligned, although it occasionally renders them as raw code blocks.
* **Weaknesses:** Analysis of hybrid routing logs shows that `marker` can sometimes produce empty pages from JSON payloads, indicating it occasionally struggles or crashes on complex or poorly formed geometry.

### MinerU
* **Strengths:** Deeply geometric and structured. The `model.json` it produces is incredibly detailed, outputting bounding box polygons (`poly`) and category/layout tags for every single visual block, equation, and image. It captures high-quality cropped images natively.
* **Weaknesses:** It appears fragile in edge cases. Review of `router_decisions.jsonl` from experimental waves consistently showed `mineru` failing with `"Extractor 'mineru' produced no parseable output."` It also outputs a very flat markdown structure without explicitly reconstructing complex table layouts as cleanly as Marker.

---

## The Hybrid Router Pipeline

To maximize parsing fidelity and robustness, we will adopt a page-by-page routing mechanism.

### 1. Page-Level Feature Classification
Before parsing, perform a fast, cheap pre-pass using `PyMuPDF` to classify page features:
* **Character count / text density**
* **Raster dominance** (Is it mostly images/scans?)
* **Table-likeness** (gridlines, whitespace structure)

### 2. Dynamic Routing Policy
Based on the extracted page features, the router will select the most appropriate engine:
* **Table-Heavy / Dense Layout Pages:** Route to **Marker** (or **MinerU**, pending stability fixes) because layout-first parsers handle complex boundaries and tables significantly better.
* **Text-Heavy / Single Column Pages:** Route directly to **PyMuPDF**. It is vastly faster and geometry-first, completely side-stepping layout-parser hallucinations and timeouts.
* **Scan-Heavy / Low Embedded Text:** Route to an OCR-assisted path.

### 3. Strict Fallback Chain
Because layout parsers are inherently brittle, we must establish a definitive fallback chain to prevent data loss. For instance, if a page is deemed complex:
1. **Primary Layout Parser:** `mineru`
2. **Secondary Layout Parser:** `marker` (Invoked if MinerU times out or yields unparseable output)
3. **Geometry/Text Parser:** `PyMuPDF` (The ultimate safety net)

### 4. Normalized Output Contract
Regardless of which tool parses a given page, the pipeline must standardize all outputs into a uniform `ParsedDocument` JSON schema before downstream chunking occurs. 

---

## Implementation & Operationalization (Experiment Harness)

To operationalize and test this hybrid approach, we will leverage the existing experiment harness.

### Configuration
* **Configure the Hybrid Runner:** Use the predefined TOML variants (e.g., `docs/features/experiment/variants/hybrid-wave2-mineru-marker-pypdf.toml` or `hybrid-wave2-mineru-marker-m4.toml`) to execute the combined tools.
* **Metrics Normalization:** The pipeline will consolidate the parsed artifacts into a single `parsed_document.json` and output the final chunk representations into `chunks.jsonl`.

### Execution Steps
1. **Prepare Baseline Data:** Use a sample PDF (e.g., `data/llm-evals-course-notes-july.pdf`) to run the parsing experiment.
2. **Execute Hybrid Pipeline:** Run the pipeline with `variant = "hybrid-wave2-mineru-marker-pypdf"` to generate evaluation artifacts.
3. **Analyze Router Decisions:** Review `router_decisions.jsonl` to verify which parser won each page and track the fallback chain (e.g., MinerU failing, falling back to Marker, and potentially down to PyMuPDF).
4. **Evaluate Metrics:** Inspect the `metrics.json` outputs to evaluate non-empty content rates, failure rates, and duplicate line rates.
5. **Human/Blinded Review:** Review `chunks_review.md` to ensure passage boundaries, markdown semantics, and table formatting are intact.

### Success Criteria
* The hybrid pipeline runs successfully on the seed documents without crashing.
* Every page is successfully parsed (target `non_empty_content_rate` = 1.0).
* Fallback events are properly logged when MinerU or Marker fail.
* The resulting chunks correctly preserve reading order, tables, and section hierarchies.
