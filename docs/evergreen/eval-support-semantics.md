# Evaluation Support Semantics for MVP Document-Grounded QA

**Status:** Draft  
**Scope:** MVP / Version 1  
**Last updated:** 2026-03-09  
**Related docs:** `mvp.md`, `eval-vocabulary.md`, `eval-scenario-taxonomy.md`, `eval-failure-taxonomy.md`  
**Authority note:** This file is the evergreen source of truth for support-state criteria, citation expectations, and honest abstention.

---

## 1. Support-state criteria

### 2.1 Sufficient support

Use **sufficient support** when the available evidence set justifies the requested claim or answer shape at MVP trust standards.

Criteria:

- the corpus contains an evidence set that materially supports the answer;
- the evidence covers the material claims required by the question at the scope the answer presents;
- no essential step depends on unsupported external inference;
- the answer can remain within the supported scope without speculative gap-filling;
- the cited anchors can take a reviewer to the relevant support.

Implications for answer behavior:

- a direct answer is allowed;
- paraphrase is allowed;
- synthesis is allowed if all material subclaims remain supported;
- uncertainty language is optional, not required.

### 2.2 Partial support

Use **partial support** when the corpus supports only a narrower, incomplete, qualified, or lower-confidence answer.

Criteria:

- some relevant evidence exists, but it does not justify the full requested answer;
- the corpus supports a subset of the requested claim, a narrower scope, or an answer direction rather than a complete conclusion;
- at least one material gap remains if the answer were stated fully;
- a fully confident answer would overstate what the evidence warrants.

Implications for answer behavior:

- the system should qualify the answer;
- the system may narrow scope explicitly;
- the system may answer only the supported subpart;
- the system must not silently fill unsupported gaps from model priors.

### 2.3 Insufficient support

Use **insufficient support** when the corpus does not provide adequate evidence for the requested claim at the requested scope.

Criteria:

- no evidence set in the corpus justifies the claim;
- retrieved text is absent, only weakly related, or too incomplete to support the conclusion;
- the question requires evidence types or external knowledge outside MVP scope;
- sources are too contradictory or too fragmentary to justify a claim without speculative reconciliation.

Implications for answer behavior:

- full abstention is valid and usually preferred;
- a narrower answer is allowed only if it is clearly labeled as narrower than the original request;
- the system must not convert weak relevance into apparent support.

---

## 3. Support-state labeling rules

- Support state is about evidence sufficiency, not about answer polish.
- Support state is judged against the active corpus, not against what a human happens to know.
- Support state should be evaluated at the level of the requested answer shape, not only at the level of topical relevance.
- A plausible answer may still be unsupported.
- A non-answer may still be the correct behavior for an insufficient-support case.

### 3.1 Derived terms

The harness may also use these derived terms in scorecards and rubrics:

- **correct abstention**: the system abstains when support is genuinely insufficient;
- **unnecessary abstention**: the system abstains even though sufficient support exists in the corpus;
- **overreach**: the system answers beyond the actual support state;
- **scope narrowing**: the system explicitly reduces the answer scope to match partial support.

`correct abstention` may still coexist with an upstream retrieval failure if the corpus did contain support but the system failed to retrieve it. In that case, abstention is preferable to fabrication at the answer layer, but the end-to-end case may still fail overall.

---

## 4. Citation expectations by source type

### 4.1 Common citation requirements

All citations, regardless of source type, must satisfy these baseline conditions:

- they identify the correct contributing document;
- they resolve to a useful inspection point at MVP granularity;
- they are materially consistent with the claim or answer fragment they support;
- they do not imply stronger support than the evidence provides;
- they do not fabricate anchors, sections, or provenance.

### 4.2 PDF citation expectations

For PDF sources, citation usefulness is judged against coarse but inspectable provenance.

Minimum acceptable shape:

- document identity or display title;
- page number;
- optionally inferred heading or section path when available.

Preferred shape:

- document identity;
- page number;
- inferred heading, section path, chapter, or other localizing label when recoverable.

Evaluation rule:

A PDF citation is useful if a reviewer can land on the correct page and find the relevant support without excessive searching.

Explicit MVP limits:

- exact paragraph-span citations are not required;
- layout-perfect anchors are not required;
- coarse provenance is acceptable if it remains inspectable and materially correct.

### 4.3 Markdown citation expectations

For Markdown sources, citation usefulness is judged against heading structure and source-local navigation.

Minimum acceptable shape:

- document identity or display title;
- heading, section path, or other stable local locator.

Preferred shape:

- document identity;
- heading path or nested section path;
- optionally a passage identifier or source-local anchor if the product exposes one.

Evaluation rule:

A Markdown citation is useful if a reviewer can navigate to the right file and locate the supported material through stable document structure without excessive searching.

### 4.4 Cross-document synthesis citation expectations

When an answer synthesizes across multiple documents:

- the citation bundle should expose all materially contributing documents;
- the answer should not collapse multi-source support into a single-source citation unless only one source actually supports the material claim;
- when sources differ, the answer should qualify the synthesis rather than present false consensus.

### 4.5 Source-navigation expectations

In source-navigation cases, citation quality is part of the primary product behavior.

For these cases, citations should be judged more strictly on:

- localizability;
- inspection value;
- whether the cited location is where the topic is actually discussed.

### 4.6 Citation anti-patterns

The following should be treated as evaluation failures:

- citation to the wrong document;
- citation to the correct document but wrong region;
- citation so broad that inspection becomes impractical;
- citation bundle that omits a necessary contributing source;
- fabricated heading, section, or page reference;
- citation that makes an unsupported claim appear grounded.

---

## 5. Honest abstention for MVP

### 5.1 Definition

**Honest abstention** is answer behavior that accurately reflects the limits of corpus support instead of manufacturing a stronger answer than the evidence warrants.

For MVP, honest abstention includes three acceptable modes:

1. **full abstention**: the system states that the corpus does not provide enough support for the requested claim;
2. **scoped abstention**: the system declines the full request but answers a narrower supported subpart;
3. **qualified uncertainty**: the system gives a partial answer while explicitly labeling the evidential limitation.

### 5.2 When honest abstention is required

Honest abstention is required when:

- the support state is insufficient;
- the available evidence is only weakly related or fragmentary;
- the requested scope exceeds what the corpus supports;
- the answer would otherwise rely on unsupported synthesis or external knowledge;
- sources conflict or are incomplete such that a confident answer would overclaim.

### 5.3 What honest abstention should say

An honest abstention should make the boundary visible.

It should communicate one or more of the following:

- that the uploaded corpus does not provide enough support;
- that only a narrower or partial answer is supported;
- what part is supported versus unsupported;
- where the nearest relevant evidence is, if any exists.

A compliant abstention does not need a fixed phrase, but it must be explicit enough that a user would not mistake it for a supported answer.

### 5.4 What honest abstention must not do

Honest abstention must not:

- give a confident answer after admitting support is weak;
- cite weakly related material as if it were decisive support;
- hide the unsupported portion behind vague language;
- fabricate provenance;
- imply exhaustive absence when the corpus merely lacks enough support to conclude.

### 5.5 Relationship to evaluation outcomes

Honest abstention is a success mode when the case genuinely has insufficient support.

However:

- abstention is not automatically a full system success if sufficient support existed in the corpus but the system failed to retrieve it;
- in that case, the answer behavior may be safer than fabrication, but the retrieval or end-to-end evaluation may still fail.

### 5.6 Working examples

#### Example A: correct abstention

Question: "Which chapter proves theorem X?"  
Corpus reality: theorem X is never discussed.  
Correct behavior: state that the uploaded documents do not contain enough support and do not invent a chapter citation.

#### Example B: scoped abstention under partial support

Question: "What exact deployment limits does the book prescribe?"  
Corpus reality: the text describes qualitative trade-offs but does not give numeric limits.  
Correct behavior: explain the qualitative guidance and explicitly say the corpus does not provide exact numeric limits.

#### Example C: incorrect non-abstention

Question: "What are the three mandatory prerequisites?"  
Corpus reality: only two are stated; a third is merely implied by unrelated context.  
Incorrect behavior: answer with three prerequisites and cite the unrelated passage as support.
