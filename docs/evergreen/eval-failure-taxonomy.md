# Evaluation Failure Taxonomy for MVP Document-Grounded QA

**Status:** Draft  
**Scope:** MVP / Version 1  
**Last updated:** 2026-03-10  
**Related docs:** `mvp.md`, `eval-vocabulary.md`, `eval-support-semantics.md`  
**Authority note:** This file is the evergreen source of truth for failure classes, examples, and release-relevant interpretation.

---

## 1. Purpose

Failure must be modeled explicitly. The harness cannot diagnose regressions or compare prototype variants if every bad result is reduced to generic quality loss.

This taxonomy exists to:

- derive targeted evaluations;
- classify regressions consistently;
- distinguish upstream and downstream failures;
- identify which design boundaries are under real pressure;
- guide mitigation ownership.

---

## 2. Taxonomy usage rules

- Classify failures by dominant cause where possible.
- Add secondary tags when needed, but do not replace the dominant class with ad hoc free text.
- Use this taxonomy across datasets, evaluator outputs, scorecards, and release discussions.
- Treat these classes as diagnostic categories, not as a single severity ranking.

---

## 3. Canonical failure classes

### 3.1 Representation failure

Use this class when the source corpus is converted into inadequate internal representations before retrieval.

Examples:

- meaningful hierarchy lost or corrupted;
- document identity unstable or missing;
- anchors missing, misleading, or unusable;
- section paths malformed;
- code blocks or table-like text flattened in ways that destroy recoverable context;
- passage inputs already semantically compromised before retrieval.

### 3.2 Segmentation failure

Use this class when structure is converted into retrieval units poorly.

Examples:

- passages too large and noisy;
- passages too small to preserve local meaning;
- semantically mixed passages;
- discourse boundaries broken;
- section relationships lost;
- adjacency unavailable for later expansion.

### 3.3 Retrieval failure

Use this class when relevant evidence is not discovered or not ranked usefully.

Examples:

- relevant evidence absent from top-k;
- partial support outranking complete support;
- retrieval dominated by noisy long passages;
- cross-document support missed;
- source-navigation retrieval returning non-resolvable fragments.

### 3.4 Context assembly failure

Use this class when good retrieval is converted into bad final context.

Examples:

- redundant overlap consuming budget;
- necessary neighbors omitted;
- unstable or incoherent ordering;
- over-concentration on one source when multi-source evidence is needed;
- truncation removing crucial support;
- citation scaffolding lost between retrieval and generation.

### 3.5 Answering failure

Use this class when the final answer misstates or exceeds the support in the available context.

Examples:

- unsupported claims;
- incorrect synthesis across evidence units;
- overconfident interpretation of ambiguous evidence;
- answering instead of abstaining;
- omission of necessary qualification.

### 3.6 Citation failure

Use this class when source references fail to support inspection even if answer text seems plausible.

Examples:

- citation points to the wrong source region;
- citation is non-resolvable;
- citation is technically present but not useful;
- citation bundle omits key contributing sources;
- citation overstates support or implies stronger grounding than exists.

### 3.7 Failure-quality failure

Use this class when the system behaves untrustworthily under weak support.

Examples:

- confident unsupported answer on insufficient-support cases;
- fabricated provenance;
- refusal to narrow scope under partial support;
- misleading certainty language under degraded retrieval;
- silent fallback to weakly related evidence.

---

## 4. Relationship to release policy

Not all failure classes are equally severe, but the following are presumptively release-blocking for MVP:

- fabricated provenance;
- repeated confident unsupported answering on insufficient-evidence cases;
- citation non-resolvability on otherwise successful answers;
- loss of mixed-format trust behavior in common cases.

Severity and gating policy may be elaborated elsewhere, but those policies should use the failure classes defined here.
