# One Design-Driving User Story for the MVP

## Story

**As an engineer working with a focused corpus of text-based PDFs and Markdown documents, I want to ask a narrow natural-language question and get either a grounded answer with inspectable source references or a clear statement that the corpus or MVP scope does not support the answer, so that I can move faster than manual search without losing trust in the result.**

## Why this should be the first design-driving story

This story captures the full MVP trust contract in one place:

- the system works over a bounded uploaded corpus;
- the answer is grounded in that corpus rather than model prior;
- the answer includes inspectable provenance;
- the system behaves honestly when support is missing, partial, ambiguous, or out of scope.

It is broader than a single eval case, but still narrow enough to drive real product decisions.

## User and job to be done

**User:** engineer reading manuals, notes, runbooks, design docs, and technical books.

**Job:** get a trustworthy answer from a small corpus faster than manual searching, then verify it quickly in the source.

## Scope boundary built into the story

Supported in MVP:

- text-based PDFs
- Markdown files
- narrow lookup, localized explanation, limited synthesis, and source navigation

Not supported as grounded answer modes in MVP:

- scanned PDFs that need OCR
- table / chart / figure / image interpretation
- external-world facts not present in the uploaded corpus

## Main success flow

1. The user uploads one or more text-based PDFs and Markdown files into one workspace.
2. The system registers each document with stable identity and preserves source type and recoverable structure.
3. The user asks a narrow question such as:
   - “What citation format is preferred for Markdown sources?”
   - “What latency target defined acceptable end-to-end performance for the study?”
4. The system retrieves the relevant passage or small evidence set.
5. The system decides that the question is supported.
6. The system returns:
   - a concise answer,
   - supporting source references,
   - enough location detail for inspection.
7. The user opens the cited source and verifies the answer quickly.

## Alternative flows

### A. Support is partial

If only part of the requested answer is supported, the system narrows the answer and labels the unsupported part rather than completing the gap.

### B. Support is missing in the corpus

If the corpus does not support the answer, the system says so explicitly rather than answering from model knowledge.

### C. The question is outside MVP scope

If the question depends on OCR-poor scans, figures, tables, charts, images, or external-world facts, the system states the limitation instead of presenting a grounded answer.

### D. Sources conflict

If relevant sources materially disagree, the system surfaces the disagreement or qualifies by source instead of silently collapsing them.

## Result shape

A valid result is not just answer text. It includes four user-visible parts:

1. **Answer artifact** — the answer itself.
2. **Citation artifact** — source references shown with the answer.
3. **Inspectable evidence path** — the user can navigate to the cited document location.
4. **Correct support-state behavior** — answer directly, narrow, qualify, surface ambiguity, or abstain.

## Minimum provenance rules in the story

- For **Markdown**, provenance should usually be **document title + section path**.
- For **PDF**, provenance should usually be **document + page**, with section path when recoverable.
- For mixed-source answers, each contributing source should have one usable provenance record.

## Acceptance criteria

1. The user can upload a small mixed-format corpus and ask one question across all files.
2. For a supported narrow question, the system answers directly.
3. The answer stays within what the retrieved evidence supports.
4. The returned provenance is inspectable, not merely document-only when finer location is recoverable.
5. The cited location actually supports the answer.
6. If support is partial, the answer is visibly narrowed or qualified.
7. If support is absent in the corpus, the system abstains explicitly.
8. If the question is out of MVP scope, the system states the limitation explicitly.
9. The user can move from answer to source with low friction.
10. The same interaction model works across Markdown, PDF, and mixed corpora.

## Primary failure risks this story should expose

- unsupported answer
- failed abstention
- weak provenance
- incorrect provenance
- wrong abstention on clearly supported lookup
- visible ingestion / structure damage
- scope-boundary dishonesty

## Design decisions this story forces

### 1. Corpus and document model

You need stable document identity, source type, title, and uploaded-corpus boundaries.

### 2. Structure and anchoring

You need section-aware structure for Markdown and coarse page-aware traceability for PDFs.

### 3. Retrieval unit design

You need retrieval passages that preserve their parent document and local anchor metadata.

### 4. Answer policy

You need an explicit answer-time decision layer:

- is the question in scope?
- what is the likely support state?
- is a direct answer justified?
- is the provenance good enough to show?

### 5. UI contract

You need an answer view plus source references that are actually navigable.

### 6. Logging and evaluation

You need traces that preserve retrieved units, answer text, provenance payload, and the answer-versus-abstain decision.

## What not to let this story expand into yet

Do not let this story pull the MVP into:

- exhaustive compare-and-contrast,
- rich table or figure understanding,
- OCR-heavy document support,
- open-web answering,
- advanced retrieval optimization as a product requirement.

## Short product principle

**The MVP succeeds when the user feels: “I can ask one focused question over my documents, get an answer I can verify, and see clearly when the system should not answer.”**
