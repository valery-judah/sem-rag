# Evaluation Support Semantics for MVP Document-Grounded QA

**Status:** Draft  
**Scope:** MVP / Version 2  
**Last updated:** 2026-03-23  
**Related docs:** `mvp.md`, `eval-vocabulary.md`, `eval-scenario-taxonomy.md`, `eval-failure-taxonomy.md`  
**Authority note:** This file is the evergreen source of truth for canonical support states, answer behavior by support state, and the minimum inspectable provenance contract.

---

## 1. Purpose

This document defines the minimum semantic contract that protects the MVP trust promise:

- the canonical support states used in evaluation;
- the answer behavior allowed for each state;
- the minimum provenance floor required for inspectable grounding.

Support state is judged against the active corpus, not against external world knowledge, and at the level of the requested answer shape rather than topical relevance alone.

---

## 2. Canonical support states

| Support state | Corpus meaning | Allowed answer behavior | Not allowed |
|---|---|---|---|
| `SUPPORTED` | The corpus contains an evidence set that materially supports the requested answer at the scope presented. | Direct answer, paraphrase, or synthesis is allowed if the answer stays within supported scope and provenance is inspectable. | Unsupported additions, fabricated support, or omission of required provenance. |
| `PARTIALLY_SUPPORTED` | The corpus supports only a subset of the requested answer, a narrower scope, or a qualified conclusion. | Answer only the supported portion, narrow scope explicitly, or qualify the unsupported portion. | Presenting the full request as fully answered or silently filling gaps from model priors. |
| `UNSUPPORTED_IN_CORPUS` | The corpus does not contain enough evidence to support the requested answer at the requested scope. | Abstain, or explicitly state that the corpus does not provide enough support. | Answering as though support exists or converting weak relevance into support. |
| `UNSUPPORTED_QUESTION_TYPE` | The question depends on an MVP-excluded capability such as external-world completion, OCR-dependent reading, or figure-first interpretation. | State the MVP limitation explicitly and avoid presenting the result as corpus-grounded. | Treating the question as in-scope and answering as though the excluded capability were supported. |
| `AMBIGUOUS_OR_CONFLICTING` | The corpus contains materially conflicting, incomplete, or unresolved evidence such that one clean answer is not justified. | Surface the ambiguity, qualify by source, or narrow to the part that is actually supported. | Selecting one confident resolution without exposing the conflict or uncertainty. |

---

## 3. Global answer-policy rules

- Do not fill evidential gaps from model priors or external knowledge.
- Do not convert weakly related text into apparent support.
- Do not hide unsupported portions behind fluent or overly complete wording.
- Do not fabricate provenance, anchors, pages, sections, or contributing sources.
- Coarse real support is acceptable for MVP; false precision is not.

---

## 4. Minimum provenance contract

The provenance floor for MVP is:

- `document_and_page` for PDF answers where page-level provenance is recoverable;
- `document_and_section` for Markdown answers where section structure is recoverable;
- one usable provenance record per materially contributing source for mixed-source answers;
- `document_page_and_section_if_available` remains valid when both are recoverable;
- `document_only` is acceptable only where the case metadata explicitly allows it.

Minimum provenance must identify the correct contributing document and a usable inspection point at MVP granularity.

The provenance contract for MVP does not require exact span anchors or layout-perfect citations. It does require inspectability and materially correct source mapping.
