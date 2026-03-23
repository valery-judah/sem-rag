# MVP Design Input v0.1 — Minimal Failure-First Specification

## Purpose

This document reframes the MVP as a small, failure-first design input for the next design phase.

It intentionally avoids a broad taxonomy and instead uses:

1. a short product contract,
2. a minimal support-state model,
3. a fixed set of first-class failures,
4. a compact use-case set,
5. a small case matrix for evaluation design.

---

## 1. Product definition

The MVP is a document question-answering and evidence-inspection service over a bounded corpus of user-uploaded:

- text-based PDF files
- Markdown files

A user should be able to:

- upload a small mixed-format corpus,
- ask a natural-language question over that corpus,
- receive an answer grounded in the corpus,
- inspect which document/page/section supports the answer,
- see explicit limitation language when the corpus or the MVP cannot support a reliable answer.

---

## 2. Product contract

The design phase should preserve five non-negotiable guarantees:

1. **Grounded answering** — answers stay within corpus support.
2. **Honest uncertainty** — partial, weak, or conflicting evidence must be qualified.
3. **Inspectable provenance** — users can inspect the supporting source location.
4. **No fabricated provenance** — no invented page, section, or support.
5. **Honest scope boundaries** — out-of-scope questions are handled explicitly.

---

## 3. In-scope behavior

Required MVP capabilities:

- ingest PDF and Markdown into one corpus,
- recover enough structure for retrieval and citation,
- retrieve across one or more documents,
- answer with source references,
- support source-grounded navigation.

Minimum structural assumptions:

- PDFs: coarse provenance such as page, and inferred heading when recoverable,
- Markdown: section path when recoverable,
- exact paragraph anchors are not required.

---

## 4. Out-of-scope behavior

The design should explicitly defer:

- OCR-dependent scanned PDFs,
- table/chart/figure/image understanding,
- external-world answers not present in corpus,
- exhaustive compare-and-contrast,
- advanced retrieval tuning and large-corpus guarantees.

---

## 5. Minimal support-state model

Each question should be classified before judging the answer:

- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `UNSUPPORTED_IN_CORPUS`
- `UNSUPPORTED_QUESTION_TYPE`
- `AMBIGUOUS_OR_CONFLICTING`

Expected behavior:

| Support state | Expected response |
|---|---|
| `SUPPORTED` | answer directly with inspectable citations |
| `PARTIALLY_SUPPORTED` | answer narrowly or qualify unsupported parts |
| `UNSUPPORTED_IN_CORPUS` | abstain or state lack of support |
| `UNSUPPORTED_QUESTION_TYPE` | state MVP limitation explicitly |
| `AMBIGUOUS_OR_CONFLICTING` | surface the ambiguity or qualify by source |

---

## 6. First-class failures for MVP

Keep these 8 as the only top-level failures:

- `U1` Unsupported answer
- `U2` Partially supported answer presented as complete
- `A1` Wrong abstention
- `A2` Failed abstention
- `P1` Provenance missing or too weak to inspect
- `P2` Incorrect provenance
- `I1` Ingestion or structure failure visible in answer quality
- `S1` Scope-boundary failure

Priority tiers:

### Tier 0 — trust breakers
- `U1`
- `A2`
- `P2`
- `S1`

### Tier 1 — strong product defects
- `U2`
- `P1`

### Tier 2 — usefulness / operability
- `A1`
- `I1`

---

## 7. Minimal use-case set

Keep only four product-facing use cases:

1. **Factual lookup**
   - Example: “What are the requirements for Z?”

2. **Localized explanation**
   - Example: “Explain the retry strategy described in these notes.”

3. **Limited multi-source synthesis**
   - Example: “What do these documents say about vector databases?”
   - Constraint: synthesis is allowed, but exhaustive reconciliation is not promised.

4. **Source navigation**
   - Example: “Where is tokenization discussed?”

Design note:
Source navigation should be treated as a first-class use case, not just citation UI.

---

## 8. Eval case design principle

Do not build a large scenario taxonomy first.

Instead, treat the eval set as a **failure-exposure plan**.

Every case should include:

- `support_state`
- `primary_target_failure`
- optional `secondary_target_failure`
- `minimum_provenance_expectation`
- `corpus_condition_tags`

Suggested tags:

- `pdf`
- `markdown`
- `mixed`
- `weak_structure`
- `conflicting_sources`
- `unsupported_scope`

---

## 9. Compact case matrix

| Case family | Support state | Source condition | Primary target failures | Correct behavior |
|---|---|---|---|---|
| supported lookup | `SUPPORTED` | `pdf` / `markdown` | `A1`, `P1`, `P2` | answer directly, cite inspectably |
| supported navigation | `SUPPORTED` | `pdf` / `markdown` | `A1`, `P1`, `P2` | route user to the right document/page/section |
| supported explanation | `SUPPORTED` | `pdf` / `markdown` | `U1`, `P1`, `P2` | explain only what evidence supports |
| partial-support synthesis | `PARTIALLY_SUPPORTED` | `mixed` preferred | `U2`, `A2`, `P1` | answer narrowly, qualify the rest |
| unsupported in corpus | `UNSUPPORTED_IN_CORPUS` | any | `A2`, `U1` | abstain or say support is missing |
| unsupported question type | `UNSUPPORTED_QUESTION_TYPE` | `pdf` / `mixed` | `S1`, `A2` | state limitation, do not answer as grounded |
| ambiguous/conflicting | `AMBIGUOUS_OR_CONFLICTING` | `mixed` preferred | `A2`, `U2`, `P1` | surface the conflict, do not collapse it |
| structure stress | varies | `weak_structure` | `I1`, `P1`, `P2`, sometimes `A1` | preserve enough structure to answer or fail honestly |

---

## 10. Provenance expectation rules

Use only a small provenance policy:

- PDF lookup/navigation: `document_and_page`
- Markdown lookup/navigation: `document_and_section`
- Mixed synthesis: one usable provenance record per contributing source
- If exactness is uncertain, prefer coarse real provenance over false precision

## 12. Recommended first build-loop suite

Start smaller than the full baseline set.

Recommended core suite: **28–36 cases**

- 8 supported lookup / navigation
- 6 partial-support
- 5 unsupported-in-corpus
- 5 unsupported-question-type
- 4 ambiguous/conflicting
- 4 weak-structure

This is enough to pressure all 8 failures without overbuilding infrastructure.

## 13. What to defer until later

Do not over-design these now:

- large secondary-cause taxonomies,
- broad scenario catalogs,
- complex KPI trees,
- exhaustive matrix coverage,
- strong compare-and-contrast behavior,
- advanced retrieval architecture.

## 14. Design-phase output this spec should drive

The next design pass should answer these concrete questions:

1. What is the retrieval unit and metadata payload?
2. How is provenance represented for PDF vs Markdown?
3. Where is support-state classification performed?
4. How does the answer policy map support state to output style?
5. How does the UI expose answer + evidence + limitation messages?
6. What traces must be logged to diagnose the 8 failures?
