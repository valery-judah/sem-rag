# Final Requirements — Query Lifecycle for MVP Document-Grounded QA

**Status:** Final draft  
**Applies to:** MVP / Version 1  
**Scope:** Query handling over a bounded corpus of user-uploaded text-based PDF and Markdown documents  
**Primary authority:** `mvp.md`  
**Subordinate design sources:** `workflow.md`, `eval-support-semantics.md`, `eval-vocabulary.md`, `21_critical_failures.md`  

---

## 1. Purpose

This document defines the final runtime requirements for the **query lifecycle** of the MVP document-grounded question-answering system.

It exists to specify, in one place, the semantic contract that the runtime must satisfy when transforming a user question into one of the following outcomes:

1. a grounded answer with inspectable citations;
2. a narrower or qualified answer that matches partial support; or
3. an explicit abstention when the corpus does not support the requested claim.

This document is intentionally written as a **contract**, not as a backlog, architecture sketch, or implementation plan. Its job is to define what the query lifecycle must preserve and what the system must prove in validation. It does not prescribe a fixed service topology, public API, storage layout, or model stack.

The query lifecycle is one of the two primary lifecycles of the system:

- the **document lifecycle**, which transforms source artifacts into stable, queryable, traceable evidence-bearing representations;
- the **query lifecycle**, which transforms a user information need into evidence retrieval, evidence selection, context assembly, support assessment, answer generation, and inspectable provenance.

The query lifecycle requirements in this document are subordinate to the MVP product boundary. They do not broaden product scope beyond:

- text-based PDF and Markdown input;
- question answering over a bounded uploaded corpus;
- grounded answering from that corpus;
- inspectable evidence and coarse provenance where exact anchors are unavailable;
- explicit abstention, qualification, or scope narrowing when support is weak, incomplete, missing, conflicting, or out of scope.

---

## 2. Product contract protected by this specification

The MVP promise is not generic chat over files. The MVP promise is:

- a user can ask a question over an uploaded bounded corpus;
- the system retrieves evidence from that corpus rather than from hidden external knowledge;
- the returned answer stays within what the evidence supports;
- the user can inspect where the answer came from; and
- when the corpus does not support the answer, the system says so honestly.

This specification protects five non-negotiable properties:

1. **Grounded answering** — user-visible claims must remain within corpus support.
2. **Honest uncertainty** — when support is partial, weak, conflicting, or missing, the system must qualify, narrow, or abstain.
3. **Inspectable provenance** — citations must resolve to useful inspection points at MVP granularity.
4. **No fabricated provenance** — the system must not invent pages, headings, sections, or source support.
5. **Honest scope boundaries** — unsupported question types or evidence demands outside MVP capability must be surfaced explicitly.

These properties govern all later requirements in this document.

---

## 3. Scope and non-scope

### 3.1 In scope

This specification covers the runtime semantics of:

- natural-language question intake over a bounded corpus;
- lightweight interpretation of the user information need;
- retrieval over evidence-bearing units produced by the document lifecycle;
- evidence selection and reranking;
- evidence-set construction across one or more documents;
- prompt/context assembly under an explicit budget;
- support-state assessment;
- answer-mode selection;
- grounded answer generation;
- citation rendering and source inspection behavior;
- insufficient-support handling;
- query-layer validation and failure classification.

### 3.2 Out of scope

This specification does not commit the system to:

- a stable public HTTP, RPC, CLI, or SDK API;
- exact scholarly citation formatting;
- exact paragraph-span or layout-perfect PDF anchoring;
- OCR, figure understanding, image question answering, or diagram interpretation;
- rich table extraction beyond what is preserved by the document lifecycle and supportable in text form;
- exhaustive compare-and-contrast across arbitrarily large corpora;
- external-world question answering;
- advanced hybrid retrieval as a mandatory MVP capability;
- architecture choices such as microservices, queues, indexing vendors, or model providers.

If a question depends on excluded capabilities, the correct behavior is explicit scope-boundary handling rather than a best-effort answer presented as grounded.

---

## 4. Authority and precedence

The following precedence rules apply:

1. `mvp.md` defines the product boundary and is authoritative on MVP scope.
2. This document defines the runtime query-lifecycle contract within that boundary.
3. `eval-support-semantics.md` is authoritative for support-state meanings, citation expectations, and honest abstention semantics.
4. `eval-vocabulary.md` is authoritative for evaluation terminology. Local synonyms must not silently replace canonical evaluation meanings.
5. `21_critical_failures.md` is authoritative for the primary MVP trust-failure labels used in validation and review.

This document may reference those sources, but it must not redefine them inconsistently.

---

## 5. Normative language

The key words **must**, **must not**, **should**, and **may** are used normatively:

- **must** / **must not**: required for conformance;
- **should** / **should not**: strongly preferred, deviation requires explicit justification;
- **may**: allowed but not required.

---

## 6. Core conceptual objects used by the query lifecycle

The query lifecycle operates on the following conceptual objects.

### 6.1 Corpus
A bounded set of source artifacts that the runtime is allowed to use as evidence.

### 6.2 Document
A source artifact with stable identity. In MVP, supported inputs are limited to text-based PDFs and Markdown documents.

### 6.3 Structure tree
A structural representation recovered during the document lifecycle, including headings, sections, paragraphs, lists, code blocks, tables when represented as text, and relative ordering.

### 6.4 Section
A heading-scoped structural container. A section is a semantic container, not necessarily the default retrieval unit.

### 6.5 Passage
A retrievable text unit aligned to discourse boundaries and token constraints. Passages are the default evidence-bearing retrieval units for MVP.

### 6.6 Anchor
A recoverable reference back to a source location. For PDFs, anchors may be coarse, such as page plus inferred heading or section path. For Markdown, anchors are typically document plus heading path or other stable local locator.

### 6.7 Evidence unit
A retrievable and referenceable source fragment that can support a claim. In MVP, this is primarily a passage, optionally enriched with section, heading, neighboring text, or other structure-derived metadata.

### 6.8 Evidence set
One or more evidence units sufficient to support a claim or answer fragment.

### 6.9 Context window
An ordered, budgeted assembly of evidence units and scaffolding sent to the generator.

### 6.10 Claim
A user-visible assertion in the answer. Claims are the unit that must be supportable.

### 6.11 Citation
A mapping from an answer or answer fragment to one or more evidence anchors. The minimum useful citation contract is document identity plus a source-type-appropriate locator; passage identifiers, snippet text, and other localizing aids are enrichments when available rather than universal minimum requirements.

### 6.12 Abstention
A valid answer mode in which the runtime declines the full request, narrows scope, or states that the active corpus does not support the requested claim.

---

## 7. Query lifecycle definition

The conceptual query lifecycle for MVP is:

`Interpret -> Retrieve -> Select -> Assemble Context -> Assess Support -> Decide Answer Mode -> Generate -> Cite or Abstain`

This is the normative runtime path.

The purpose of making **Assess Support** and **Decide Answer Mode** explicit is to prevent the generation step from becoming the hidden judge of evidence sufficiency. Retrieval, support judgment, and final rendering must remain inspectable as separate concerns.

Once support has been assessed, downstream stages may preserve that answer posture or narrow it further, but they must not escalate it into a broader or more confident answer than the evidence supports. In effect, answer-mode selection and grounded generation act as downgrade-only enforcement even if implemented without a separately named runtime guard.

The query lifecycle must therefore satisfy the following top-level rule:

> The runtime must not collapse query interpretation, retrieval, support judgment, answer generation, and citation behavior into a single opaque step that prevents inspection, testing, or failure localization.

---

## 8. Shared stage-contract model

Each lifecycle stage in this document is specified in terms of:

- **Consumes** — the inputs it depends on;
- **Emits** — the semantic outputs it produces;
- **Preserves** — the invariants it must not break;
- **Not responsible for** — downstream concerns it does not own.

This model is semantic, not implementation-specific. The runtime may realize these contracts in a single process, multiple modules, or later service boundaries, but the outputs and preserved properties must remain inspectable.

---

## 9. Stage requirements

## QL-1. Corpus-bounded query intake and interpretation

### Objective
Transform a user request into a retrieval-ready representation while preserving corpus boundaries and the answer shape implied by the request.

### Consumes
- natural-language user question;
- workspace or equivalent corpus boundary;
- runtime configuration relevant to scope or answer policy.

### Emits
- normalized query representation;
- retrieval intent or retrieval plan sufficient for downstream stages;
- answer-shape expectations at MVP-relevant granularity;
- any scope flags needed to detect unsupported question types.

### Preserves
- corpus-boundedness;
- user-requested scope as interpreted by the system;
- enough distinction among query types to avoid generic retrieval behavior for materially different tasks.

### Requirements
The runtime **must** accept natural-language questions against the bounded ingested corpus for a workspace or equivalent ownership boundary.

The runtime **must** remain explicitly corpus-bounded. It **must not** treat model priors or external-world knowledge as hidden support for user-visible claims.

The interpretation stage **must** preserve a place for the distinctions that materially affect retrieval, support assessment, and abstention behavior. At minimum, the system **must** be able to distinguish or otherwise account for:

- direct factual lookup;
- section-scoped explanation;
- one-document synthesis;
- cross-document synthesis;
- source-navigation requests;
- insufficient-support or unsupported-question-type cases.

The runtime **does not need** a heavyweight classifier for MVP. However, it **must not** erase the answer-shape distinctions required downstream.

The interpretation stage **should** preserve request attributes such as:

- desired specificity;
- whether the user asks for location rather than explanation;
- whether the user asks for a comparison or synthesis;
- whether the question implicitly requires evidence types outside MVP scope.

### Must not
The interpretation stage **must not** broaden the user request silently, downgrade a precise question into generic topical retrieval without later qualification, or infer support from topic similarity alone.

### Not responsible for
- ranking evidence;
- final support-state judgment;
- rendering the final answer.

---

## QL-2. Evidence retrieval contract

### Objective
Retrieve evidence-bearing candidates from the active corpus while preserving stable identity, structure context, and recoverable provenance.

### Consumes
- normalized query representation;
- active retrieval indexes and document-derived representations;
- corpus boundary;
- retrieval configuration.

### Emits
- ranked evidence candidates;
- candidate metadata including stable document identity and passage identity;
- enough provenance context to allow later citation and source inspection.

### Preserves
- retrieval over evidence-bearing units rather than untraceable raw text blobs;
- the retrieval hierarchy `DOCUMENT -> SECTION -> PASSAGE`;
- stable identity and recoverable provenance for each candidate.

### Requirements
Retrieval **must** operate over evidence-bearing units derived from the document lifecycle.

For MVP:

- passages **must** remain the default retrieval unit;
- sections **must** remain semantic containers rather than the default retrieval unit;
- section or heading metadata **may** supplement retrieval and later citation;
- neighboring context **may** be attached later for coherence, but the underlying passage identity **must** remain preserved;
- evidence **may** span one or more documents.

Each retrieved candidate **must** preserve enough identity to resolve back to:

- the source document;
- the passage or equivalent evidence-unit identity;
- source-local context sufficient for later citation and inspection.

Retrieval **should** preserve or expose metadata useful for later stages, such as:

- section path or heading path;
- local order within the document;
- page number or coarse page region for PDFs;
- stable local locator for Markdown.

### Must not
Retrieval **must not** emit anonymous text fragments that cannot later be mapped back to provenance.

Retrieval **must not** erase passage identity merely because neighboring text or section metadata is appended.

### Not responsible for
- final support sufficiency;
- duplicate suppression across the final evidence set;
- answer phrasing.

---

## QL-3. Evidence selection and reranking contract

### Objective
Convert raw retrieval candidates into support-oriented evidence sets suitable for answering rather than merely preserving score order.

### Consumes
- ranked retrieval candidates;
- structural metadata and provenance metadata;
- query interpretation output.

### Emits
- selected evidence units;
- selected evidence sets for one or more answer fragments;
- an explicit ordering suitable for context assembly.

### Preserves
- support completeness;
- local coherence;
- multi-document evidence when required;
- stable provenance and traceability.

### Requirements
After initial retrieval, the runtime **must** select and rerank evidence in a way that improves support quality rather than only score order.

Selection logic **must** be explicit enough to validate. At minimum it **must** account for:

- topical relevance to the interpreted question;
- support completeness versus isolated fragments;
- local coherence within section or neighboring context;
- duplicate or near-duplicate suppression;
- multi-document evidence when the question requires synthesis.

The runtime **must** support evidence sets composed of:

- a single passage for direct factual answers;
- a passage plus structural scaffolding or neighboring context for locally coherent explanation;
- multiple passages across one or more documents for synthesis answers.

The answer path **must not** assume that one claim maps to exactly one passage.

The selection stage **should** bias toward evidence sets that maximize supportability and inspectability, not merely lexical overlap or embedding similarity.

### Must not
Selection **must not** prefer one high-scoring fragment over a more complete evidence set when the latter is required to avoid overclaiming.

Selection **must not** collapse materially distinct supporting sources into a single apparent source if multiple documents are needed to support the answer.

### Not responsible for
- final context-window truncation;
- final support-state labeling;
- final answer rendering.

---

## QL-4. Context assembly contract

### Objective
Assemble a deterministic, budgeted, interpretable context window from selected evidence without destroying the support structure that upstream stages preserved.

### Consumes
- ordered evidence units or evidence sets;
- structural metadata and provenance metadata;
- prompt budget and generation constraints.

### Emits
- an ordered context window for generation;
- an auditable mapping from context contents back to selected evidence units.

### Preserves
- deterministic ordering semantics;
- identity of evidence units included in the prompt;
- local coherence required to interpret the evidence correctly;
- non-loss of crucial support due to accidental truncation.

### Requirements
Context assembly **must** use explicit ordering and budget rules.

Context assembly **must**:

- preserve deterministic ordering semantics;
- include adjacent or neighboring evidence only when it materially improves local coherence;
- remove redundant overlap where practical;
- retain section or heading context when needed to interpret the passage correctly;
- fit the configured prompt budget without silently dropping crucial support.

When truncation or omission is required due to budget, the system **must** do so intentionally rather than by incidental runtime ordering.

The assembled context **must** remain auditable: it should be possible in testing and debugging to determine which evidence units were included, in what order, and why.

### Must not
Context assembly **must not** degrade good retrieval into unsupported answering by accidental clipping, arbitrary ordering, or loss of provenance linkage.

Context assembly **must not** include neighboring text by default when it adds noise, changes interpretation, or consumes budget without improving support.

### Not responsible for
- determining whether the assembled context is sufficient to answer the question;
- deciding whether to abstain;
- rendering citations.

---

## QL-5. Support assessment contract

### Objective
Determine the support state of the assembled evidence relative to the requested answer shape before answer rendering.

### Consumes
- assembled context window;
- selected evidence sets and provenance metadata;
- interpreted answer shape;
- support-state semantics from the evergreen evaluation contract.

### Emits
- support-state assessment;
- rationale sufficient for validation and downstream answer-mode selection;
- any narrowing or qualification boundary implied by the evidence.

### Preserves
- separation between evidence sufficiency judgment and language generation;
- canonical support-state meanings;
- alignment between answer scope and evidence scope.

### Requirements
The query lifecycle **must** contain an explicit support-assessment stage.

Support assessment **must** evaluate evidence sufficiency against the **requested answer shape**, not merely topical relevance.

Support assessment **must** use the canonical support-state meanings already defined for MVP. At minimum, downstream behavior must support the equivalent of:

- `SUPPORTED`;
- `PARTIALLY_SUPPORTED`;
- `UNSUPPORTED_IN_CORPUS`;
- `UNSUPPORTED_QUESTION_TYPE`;
- `AMBIGUOUS_OR_CONFLICTING`.

The assessment **must** distinguish among:

- evidence that materially supports a direct answer;
- evidence that supports only a narrower or qualified answer;
- evidence that is relevant but insufficient;
- evidence demands outside MVP scope;
- evidence that is conflicting or too fragmentary to justify a confident claim.

A plausible answer **must not** be treated as supported merely because the retrieved text is topically related.

### Must not
Support assessment **must not** be left implicit inside answer generation.

Support assessment **must not** equate retrieval success with evidence sufficiency.

### Not responsible for
- answer wording;
- citation formatting.

---

## QL-6. Answer-mode decision contract

### Objective
Select the correct response mode from the assessed support state before natural-language rendering.

### Consumes
- support-state assessment;
- interpreted user request;
- selected evidence and provenance.

### Emits
- answer policy decision, such as direct answer, qualified answer, narrowed answer, explicit abstention, or explicit scope-boundary response.

### Preserves
- honest uncertainty;
- alignment between evidence strength and answer posture;
- explicit visibility of support limitations.

### Requirements
The lifecycle **must** choose answer behavior according to support state.

After support state is determined, later stages **must not** widen the answer beyond that state. They may keep the same posture, narrow scope further, add qualification, or abstain more conservatively, but they **must not** convert partial, conflicting, unsupported, or out-of-scope cases into a broader supported-answer posture.

The required high-level behavior is:

| Support state | Required answer-mode behavior |
|---|---|
| `SUPPORTED` | answer directly and cite inspectable support |
| `PARTIALLY_SUPPORTED` | answer narrowly, qualify the unsupported portion, or both |
| `UNSUPPORTED_IN_CORPUS` | abstain or state that the corpus does not provide enough support |
| `UNSUPPORTED_QUESTION_TYPE` | explicitly state the MVP capability boundary |
| `AMBIGUOUS_OR_CONFLICTING` | surface the ambiguity, difference by source, or unresolved conflict |

The answer-mode stage **must** allow at least three abstention-compatible behaviors:

1. **full abstention**;
2. **scoped abstention**;
3. **qualified uncertainty**.

### Must not
The system **must not** give a complete, confident answer where only partial support exists.

The system **must not** answer an unsupported question type as if it were an in-scope grounded answer.

### Not responsible for
- the final phrasing of the answer;
- exact citation layout.

---

## QL-7. Grounded answer generation contract

### Objective
Render answer text that remains constrained by retrieved evidence and the chosen answer mode.

### Consumes
- answer-mode decision;
- supportable evidence from the assembled context;
- provenance and citation candidates;
- generation configuration.

### Emits
- answer text;
- answer-fragment to evidence linkage sufficient for later citation rendering and review.

### Preserves
- groundedness;
- scoped behavior under partial support;
- abstention honesty;
- traceability from answer back to evidence.

### Requirements
Generation **must** produce answer text constrained by the retrieved evidence and answer mode.

At minimum:

- supported answers **must** be materially grounded in the assembled context;
- answer text **may** synthesize across sources when the evidence supports the synthesis;
- the system **must not** overstate what the evidence supports;
- the answer **must** preserve enough linkage to explain why it was returned;
- unsupported portions **must not** be filled silently from model priors.

When partial support exists, generation **must** make the boundary visible rather than burying it in vague language.

When sources conflict or diverge, generation **must** qualify the result rather than flattening disagreement into false consensus.

### Must not
Generation **must not** fabricate claims, source support, or certainty not justified by the assessed support state.

Generation **must not** convert weak relevance into the appearance of strong support.

### Not responsible for
- discovering evidence that retrieval failed to surface;
- inventing missing provenance.

---

## QL-8. Citation rendering and source inspection contract

### Objective
Render inspectable citations that map supported answer content back to useful source locations at MVP granularity.

### Consumes
- answer output and answer-fragment linkage;
- selected evidence units;
- provenance metadata and anchors.

### Emits
- citations or citation bundles attached to supported answer content;
- enough source-local detail for a reviewer or user to inspect support.

### Preserves
- provenance correctness;
- usefulness for inspection;
- alignment between cited source and supported claim.

### Requirements
Supported answers **must** include inspectable citations at useful MVP granularity.

For MVP, the mandatory citation minimum is recoverable provenance that lets a reviewer inspect the supporting source region at useful granularity. That minimum **must** include source identity plus a source-type-appropriate locator.

Recommended citation enrichments **may** also be included when the runtime preserves them and product surfaces allow them, such as:

- passage or chunk identity when retained by the system;
- section identity or heading path when recoverable;
- page label or coarse page location for PDFs when recoverable;
- supporting snippet text or equivalent localizing aid when product surfaces allow it.

Citation behavior **must** follow source-type expectations:

#### For PDF sources
Minimum acceptable citation shape:

- document identity or title;
- page number.

Additional PDF localizers, such as inferred heading or section path, are recommended when recoverable but are not part of the universal minimum.

A PDF citation is acceptable only if a reviewer can land on the correct page and locate the relevant support without excessive searching.

#### For Markdown sources
Minimum acceptable citation shape:

- document identity or title;
- heading path, section path, or other stable local locator.

Additional Markdown localizers, passage identifiers, or snippet text are recommended enrichments when available, but the minimum remains document identity plus a stable local locator.

A Markdown citation is acceptable only if a reviewer can navigate to the correct file region without excessive searching.

#### For cross-document synthesis
When multiple documents materially support a claim, the citation bundle **must** expose all materially contributing sources. The runtime **must not** collapse multi-source support into a single-source citation unless only one source actually supports the claim.

### Must not
Citations **must not**:

- point to the wrong document;
- point to the correct document but wrong region;
- be so broad that inspection becomes impractical;
- omit a necessary contributing source in a synthesis answer;
- fabricate page, section, heading, or anchor information;
- make unsupported content appear grounded.

### Not responsible for
- deciding whether a claim is supportable;
- replacing honest abstention when support is insufficient.

---

## 10. Cross-cutting invariants

The following invariants apply across the full query lifecycle.

### 10.1 Corpus-bounded behavior
The runtime **must** answer from the active uploaded corpus. External-world knowledge **must not** be used as hidden evidence.

### 10.2 Passage-first retrieval semantics
The default retrievable evidence unit **must** remain the passage. Sections are semantic containers and citation scaffolding, not the default retrieval unit.

### 10.3 Recoverable provenance
Every evidence unit that materially contributes to an answer **must** remain recoverably linked to source provenance sufficient for MVP inspection.

### 10.4 Evidence-to-answer traceability
It **must** be possible to audit supported user-visible answers back to retrieved evidence units and then back to source provenance.

### 10.5 Deterministic ordering
Given identical corpus content, configuration, and retrieval inputs, ordering behavior **must** be deterministic where feasible and otherwise stable enough for regression analysis.

At minimum, the system **must** make explicit:

- retrieval result ordering rules;
- tie handling;
- duplicate suppression behavior;
- context assembly order.

### 10.6 Honest insufficiency behavior
When support is insufficient, the runtime **must** abstain, narrow, qualify, or otherwise surface the evidence boundary honestly. It **must not** hide insufficiency behind confident prose.

### 10.7 No fabricated support artifacts
The runtime **must not** fabricate claims, citations, pages, headings, sections, or other provenance artifacts.

### 10.8 Multi-source honesty
When the answer depends on multiple sources, the runtime **must** preserve that multiplicity rather than presenting the result as if one source were solely sufficient.

### 10.9 Layered failure visibility
Failures **must** remain localizable to query interpretation, retrieval, selection, context assembly, support assessment, answer generation, or citation behavior rather than disappearing into a single opaque failure bucket.

---

## 11. Support-state semantics adopted by the query lifecycle

This section operationalizes, but does not redefine, the support semantics used by MVP evaluation.

### 11.1 Sufficient support
Use sufficient support when the corpus contains an evidence set that materially supports the answer at the scope the answer presents.

Implications:

- a direct answer is allowed;
- paraphrase is allowed;
- synthesis is allowed when material subclaims remain supported;
- confidence language is optional, not required.

### 11.2 Partial support
Use partial support when the corpus supports only a narrower, incomplete, or qualified answer.

Implications:

- the answer should qualify the unsupported portion;
- the answer may explicitly narrow scope;
- the system may answer only the supported subpart;
- unsupported gaps must not be filled silently.

### 11.3 Insufficient support
Use insufficient support when the corpus does not justify the requested claim at the requested scope.

Implications:

- full abstention is valid and usually preferred;
- a narrower answer is allowed only if it is clearly labeled as narrower than the request;
- weak relevance must not be converted into apparent support.

### 11.4 Ambiguous or conflicting support
Use ambiguous or conflicting support when source material is divergent, contradictory, or too fragmentary to justify a single clean claim without qualification.

Implications:

- the answer should surface the ambiguity or source-specific difference;
- the answer should not collapse conflict into false consensus;
- citations should expose the differing sources where feasible.

### 11.5 Unsupported question type
Use unsupported question type when the request depends on evidence modalities or product capabilities outside MVP scope.

Implications:

- the system should state the scope boundary explicitly;
- the system should not produce a grounded answer posture for an unsupported question type.

---

## 12. Answer-policy rules

The following answer-policy rules are mandatory.

### 12.1 Direct answer rule
A direct answer is permitted only when support is sufficient for the answer scope actually presented.

### 12.2 Qualification rule
If the requested answer shape is broader than the available support, the system must qualify or narrow the answer explicitly.

### 12.3 Abstention rule
If no evidence set justifies the requested claim, the system must abstain rather than speculate.

### 12.4 Scope-boundary rule
If the question requires unsupported capabilities, the system must state that boundary explicitly rather than failing silently or answering as if in scope.

### 12.5 Conflict rule
If sources conflict materially, the answer must surface the conflict or uncertainty rather than presenting a single unqualified conclusion.

### 12.6 Citation coupling rule
Supported answer content must have inspectable citation support at the minimum contract of source identity plus a source-type-appropriate locator. Unsupported or abstained content must not be decorated with fabricated or misleading citations.

---

## 13. Provenance and inspection requirements

### 13.1 Minimum provenance expectation by source type
For MVP, minimum provenance expectations are:

- **PDF**: document identity plus page number;
- **Markdown**: document identity plus heading path, section path, or other stable local locator;
- **Mixed-format synthesis**: one usable provenance record per materially contributing source;
- **Optional enrichments**: passage or chunk identity when retained by the runtime; supporting snippet text or equivalent localizing aid when product surfaces allow it.

### 13.2 Inspection usefulness standard
A citation is useful only if a reviewer can reach the correct source area and locate the supporting material without excessive searching.

### 13.3 Traceability standard
For every supported answer, the system **must** preserve:

- linkage from the answer or answer fragment to one or more evidence units;
- linkage from those evidence units to source provenance;
- enough explanation in logs, traces, or review harness output to reconstruct why the answer was returned.

Exact claim-span alignment is not required for MVP, but auditable support is required.

---

## 14. Determinism and stability requirements

The lifecycle **must** behave deterministically where feasible and otherwise remain structurally stable enough for regression analysis.

At minimum:

- retrieval ordering rules **must** be explicit;
- score ties **must** break deterministically;
- duplicate suppression **must** be intentional and repeatable;
- context assembly order **must not** depend on incidental runtime iteration order;
- answer-mode selection **must** be reproducible from support-state inputs.

Model sampling behavior may remain probabilistic where unavoidable, but the system should minimize non-determinism that hides semantic regressions.

---

## 15. Failure-handling contract

The runtime must preserve failure quality by making query-path failures inspectable at the correct layer.

### 15.1 Primary MVP trust failures
Validation and review **must** be able to represent the following primary trust failures:

- `U1` — unsupported answer;
- `U2` — partially supported answer presented as complete;
- `A1` — wrong abstention;
- `A2` — failed abstention;
- `P1` — provenance missing or too weak to inspect;
- `P2` — incorrect provenance;
- `I1` — ingestion or structure failure visible in answer quality;
- `S1` — scope-boundary failure.

### 15.2 Diagnostic internal failures
The runtime or harness **should** also preserve diagnostic causes such as:

- retrieval miss or low-quality evidence discovery;
- evidence fragmentation or poor segmentation boundaries;
- context assembly degradation;
- unsupported synthesis or answer overreach;
- citation mismatch;
- normalization or structure-recovery failure.

These diagnostic labels do not replace the user-visible primary failure; they explain it.

### 15.3 Local failure principle
The system **must** fail locally and explicitly rather than returning a globally confident but weakly supported answer.

This means that, where possible:

- retrieval failure should remain visible as retrieval failure;
- evidence insufficiency should drive abstention or qualification;
- provenance failure should not be hidden behind answer fluency;
- scope-boundary failure should be surfaced as scope boundary, not as unsupported answering.

---

## 16. Validation requirements

Each stage of the query lifecycle must have validation evidence at the same semantic level as the requirement it satisfies.

### 16.1 Minimum validation surface
The validation surface **must** include:

- contract tests for retrieval-hit, evidence-unit, answer, and citation shapes;
- retrieval tests that prove ordering, provenance preservation, and traceability behavior;
- scenario tests for direct factual lookup, section-scoped explanation, one-document synthesis, cross-document synthesis, source navigation, insufficient support, conflicting support, and unsupported question type;
- failure-path tests that distinguish retrieval, context, answer, citation, and scope failures;
- review or harness outputs that can map user-visible failures onto `U1/U2/A1/A2/P1/P2/I1/S1`.

### 16.2 Stage-level validation obligations

#### QL-1 interpretation validation
Validation should prove that different question shapes produce meaningfully different downstream behavior where required.

#### QL-2 retrieval validation
Validation should prove that retrieval returns traceable evidence-bearing units and preserves enough identity for later citation.

#### QL-3 selection validation
Validation should prove that the system can prefer complete supportable evidence over isolated fragments and can combine multiple sources when needed.

#### QL-4 context validation
Validation should prove deterministic ordering, intentional truncation, and preservation of crucial evidence under prompt budget.

#### QL-5 support assessment validation
Validation should prove that support sufficiency is judged against answer shape rather than topic match.

#### QL-6 answer-mode validation
Validation should prove correct direct answer, qualification, abstention, and scope-boundary behavior for the corresponding support states.

#### QL-7 generation validation
Validation should prove that answer text does not overstate evidence and that partial support becomes visible in the answer.

#### QL-8 citation validation
Validation should prove that citations are materially correct, useful for inspection, and complete for synthesis answers.

### 16.3 Evaluation orientation
The system should be judged using layered quality rather than answer fluency alone:

- representation quality;
- retrieval quality;
- context quality;
- answer quality;
- provenance quality;
- abstention quality.

---

## 17. Delivery sequencing appendix

This appendix is informative rather than normative. It separates rollout sequencing from runtime contract.

### Stage A — query intake and retrieval
Make corpus-bounded question handling real enough to retrieve traceable evidence units from ingested content.

### Stage B — selection and context assembly
Improve evidence completeness, local coherence, and deterministic assembly under budget.

### Stage C — support assessment and answer policy
Make support-state judgment explicit and enforce correct answer posture for supported, partial, insufficient, conflicting, and out-of-scope cases.

### Stage D — grounded answer and citations
Render answers with inspectable provenance and preserve evidence-to-answer auditability.

### Stage E — validation hardening
Expand the harness to cover scenario breadth, primary failure labels, and regression stability.

This appendix exists only to aid implementation planning. Conformance is determined by the normative sections above.

---

## 18. Conformance summary

A query-lifecycle implementation conforms to this specification only if it can, for an MVP-scoped question over an ingested bounded corpus:

1. interpret the question without leaving the corpus boundary;
2. retrieve traceable evidence-bearing units;
3. select evidence sets rather than isolated fragments when needed;
4. assemble context deterministically under budget;
5. assess support explicitly against the requested answer shape;
6. choose the correct answer mode for the support state;
7. generate grounded answer text without unsupported overreach; and
8. provide inspectable citations when supported content is returned, or honest abstention when it is not.

If any of those properties fails, the runtime may still produce fluent output, but it does not satisfy the MVP query-lifecycle contract.
