# RAG Delivery Workflow Rewrite

## Status
Draft

## Purpose

This document rewrites the delivery workflow for the MVP RAG system.

The prior direction was still too close to a conventional engineering workflow: frame the work, decompose it into domains, and then implement toward an intended architecture. That is the wrong center of gravity for this stage.

For an early document-grounded RAG system, implementation is cheap and architecture certainty is low. The durable value is not the first codebase. The durable value is a correct conceptual model of the system, a clear evidence model, a stable set of invariants, and a validated understanding of which boundaries are real.

The workflow therefore shifts from **architecture-first delivery** to **model-first, prototype-assisted architectural discovery**.

The core idea is simple:

1. Model the RAG system precisely.
2. Make evidence, retrieval units, claims, and failures first-class concepts.
3. Derive bounded contexts and contracts from that model.
4. Build a thin integrated prototype to pressure the model.
5. Extract the minimal durable architecture only after the running system exposes the true seams.

This document focuses on conceptual structure, domain modeling technique, and the bridge from modeling to delivery. It intentionally avoids detailed operational mechanics, artifact catalogs, and later productionization policy.

---

## 1. Why this workflow exists

The workflow exists to solve a specific problem: early RAG systems fail when teams optimize for implementation shape before they understand the semantics of the system they are building.

This is especially true for document-grounded assistants. In this kind of system, correctness is not determined by API shape or service boundaries alone. It depends on whether the system can:

- preserve source structure well enough to support precise retrieval,
- produce retrieval units that remain semantically coherent,
- map generated claims back to supporting evidence,
- assemble context without destroying relevance or wasting budget,
- fail honestly when the corpus cannot support an answer.

A workflow that begins from implementation topology will usually miss these pressures. It tends to produce premature service boundaries, accidental contracts, and weak evaluation loops. A workflow that begins from the system model is better aligned with the actual source of quality.

This rewrite therefore treats early implementation as an instrument for learning. The purpose of delivery is not to defend the first architecture. The purpose is to discover the smallest architecture that can preserve the essential semantics of the system under realistic pressure.

---

## 2. System thesis: what kind of system we are building

We are not building a generic "chat over files" feature.

We are building a **document-grounded RAG system** whose behavior is defined by controlled evidence flow through two connected lifecycles:

1. the **document lifecycle**, which transforms source artifacts into stable, queryable knowledge representations;
2. the **query lifecycle**, which transforms a user information need into evidence selection, context assembly, and a grounded answer or abstention.

The product promise is:

- the system accepts a bounded corpus of documents,
- preserves enough source structure to keep evidence traceable,
- retrieves the most relevant evidence for a question,
- assembles coherent context within a token budget,
- generates answers whose claims are supported by retrieved evidence,
- and abstains or narrows scope when the evidence is insufficient.

This thesis has several implications.

First, the system is fundamentally **evidence-constrained**. Generation quality depends on upstream representation quality and retrieval behavior.

Second, the system is fundamentally **structure-sensitive**. A poor parser or segmenter can silently destroy later answer quality.

Third, the system is fundamentally **traceability-sensitive**. If evidence cannot be mapped back to anchors in the source corpus, citation quality and trust collapse.

Fourth, the system must be designed around **layered quality**, not only answer-level quality. Representation quality, retrieval quality, context quality, and answer quality are distinct concerns.

This thesis should govern every later modeling and implementation decision.

---

## 3. Conceptual model of the system

The workflow should begin by fixing the conceptual objects of the system before discussing domain boundaries or code structure.

### 3.1 Core objects

The minimum conceptual vocabulary should include the following:

#### Corpus
A bounded collection of source artifacts that the system is allowed to use as evidence.

#### Document
A source artifact with stable identity. A document may be PDF, Markdown, HTML, wiki content, or another supported source format.

#### Document version
A specific content snapshot of a document. Some identities should remain stable across re-ingestion, while content-derived structures may vary by version.

#### Structure tree
A structural representation of the document after parsing. This includes headings, sections, paragraphs, lists, tables, code blocks, and relative ordering.

#### Section
A heading-scoped subtree in the structure tree. A section is a semantic container, not necessarily a retrieval unit.

#### Passage
A retrievable text unit aligned to discourse boundaries and token constraints. Passages are typically the primary evidence units for retrieval.

#### Anchor
A stable reference that can resolve back to a source location within the document or its rendered form.

#### Evidence unit
A retrievable or referenceable source fragment that can support a claim. In the first version this is usually a passage, sometimes section metadata, and later may include table cells, code snippets, or graph-linked evidence.

#### Evidence set
A set of one or more evidence units sufficient to support a user-visible claim or answer fragment.

#### Context window
An assembled set of evidence units, ordered and budgeted for generation.

#### Query intent
The information need implied by a user request. In early versions the system may not formally classify this, but the model should still acknowledge it.

#### Claim
A user-visible assertion in the answer. Claims are the unit that must be supportable.

#### Citation
A mapping from a claim or answer span to one or more evidence anchors.

#### Abstention
A valid answer mode in which the system declines to answer fully, narrows scope, or states that the current corpus does not support the requested claim.

### 3.2 Primary lifecycles

The model should also fix the primary lifecycles.

#### Document lifecycle

A document moves through the following conceptual path:

`Acquire -> Parse -> Structure -> Segment -> Represent -> Index/Publish`

This lifecycle is responsible for creating stable, retrievable, anchorable evidence-bearing objects.

#### Publication and mutation lifecycle

The model must also define what happens after a document version has been published:

`Publish -> Re-ingest/Supersede -> Re-index -> Withdraw/Delete from active retrieval`

This lifecycle is responsible for preserving stable document identity, version lineage, and citation resolvability as content changes over time. Superseded or withdrawn material may leave active retrieval while still remaining traceable enough for audit and regression analysis.

#### Query lifecycle

A query moves through the following conceptual path:

`Interpret -> Retrieve -> Select/Rerank -> Assemble Context -> Generate -> Cite or Abstain`

This lifecycle is responsible for ensuring that the final answer is constrained by the available evidence.

### 3.3 Why the conceptual model must precede domain design

If domains are defined before the conceptual model, teams usually mistake implementation convenience for system truth. They define services or modules around tools, frameworks, or repo boundaries instead of around the semantics that must be preserved.

The workflow should therefore force this order:

1. conceptual vocabulary,
2. lifecycles,
3. invariants,
4. evidence semantics,
5. bounded contexts,
6. implementation.

That order reduces accidental architecture and keeps the delivery process aligned with actual product behavior.

---

## 4. RAG-specific quality model

The workflow must define quality at the right levels.

A common failure mode in RAG work is to judge the system only by final answer quality. That is insufficient. The answer is the end of a chain whose upstream failures may be hidden or misattributed.

The workflow should model quality across at least five layers.

### 4.1 Representation quality

This asks whether the system produced good knowledge representations from the source corpus.

Key concerns:

- Was meaningful document structure preserved?
- Were sections, lists, tables, and code blocks handled without destroying semantics?
- Are anchors resolvable and precise enough for citation?
- Are IDs stable enough to support traceability and bounded churn?

A poor answer may originate here long before retrieval or generation.

### 4.2 Retrieval quality

This asks whether the system found the right evidence.

Key concerns:

- Did the top-ranked results contain the needed evidence?
- Did passage boundaries help or hurt semantic matching?
- Did retrieval return complete support or only fragments?
- Did hierarchy-aware expansion improve coherence?

Retrieval quality should be understood as evidence discovery quality, not merely search ranking quality.

### 4.3 Context quality

This asks whether the retrieved evidence was assembled into a usable prompt context.

Key concerns:

- Is the context ordered coherently?
- Is redundant overlap removed?
- Are adjacent passages included when needed for local coherence?
- Does the final context fit budget constraints without losing crucial support?

Poor context assembly can turn good retrieval into bad generation.

### 4.4 Answer quality

This asks whether the user-visible answer is correct and well-supported.

Key concerns:

- Are the answer claims materially correct?
- Is each claim supported by retrieved evidence?
- Are citations accurate and useful?
- Does the answer overstate what the evidence warrants?

### 4.5 Failure quality

This asks whether the system fails in trustworthy ways.

Key concerns:

- Does the system abstain when evidence is absent or weak?
- Does it expose uncertainty instead of inventing support?
- Does it avoid false confidence when retrieval is degraded?
- Does it fail locally and explicitly rather than producing globally misleading output?

Failure quality is a first-class dimension. In a grounded assistant, honest non-answer behavior is part of the product contract.

### 4.6 Consequence for workflow design

Because quality is layered, the workflow must not jump directly from "user scenario" to "app implementation." It must preserve the ability to reason about where failure originates.

That requires a delivery approach built on explicit modeling of representations, evidence, retrieval units, claims, and failures.

---

## 5. Domain modeling method for this product

The workflow should specify an explicit domain modeling method suited to a RAG system.

This method should not start from code modules or infrastructure. It should begin from information behavior and only later resolve into bounded contexts.

### 5.1 Modeling order

The recommended order is:

1. define the product promise,
2. define the conceptual objects,
3. model end-to-end scenarios,
4. model evidence semantics,
5. define invariants,
6. model failure modes,
7. derive bounded contexts,
8. derive contracts,
9. validate the model with a running prototype.

This ordering matters because it keeps the model grounded in user-visible behavior and evidence flow.

### 5.2 Recommended modeling techniques

The following techniques fit this problem well.

#### Scenario modeling
Use realistic end-to-end scenarios as the primary pressure on the model. Scenarios should represent actual information-seeking behavior against a bounded corpus.

#### Ubiquitous language definition
Define a shared vocabulary for objects like document, section, passage, anchor, evidence set, claim, citation, abstention, and context window. Ambiguous terms should be eliminated early.

#### Event-flow or lifecycle mapping
Map the conceptual transitions in the document and query lifecycles. This helps expose state transitions, handoffs, and failure points.

#### Invariant modeling
Identify truths that must survive all rewrites. This is where stable identity, anchorability, and deterministic ordering belong.

#### Failure-mode modeling
Treat failure classes as part of the domain rather than as downstream defects. Unsupported claims, anchor mismatch, retrieval miss, and evidence fragmentation should be modeled explicitly.

#### Bounded context mapping
Only after the above steps, define subsystem boundaries. Those boundaries should be derived from what the model requires, not from implementation habits.

### 5.3 What the method rejects

This workflow explicitly rejects several starting moves:

- decomposing the system into services before evidence semantics are defined,
- writing domain-local use cases before end-to-end scenario pressure is understood,
- defining API contracts before the core object model is stable,
- treating generation as the product center while leaving retrieval and evidence under-modeled.

These moves create avoidable ambiguity and lead to architectures that look organized but do not preserve grounded behavior.

---

## 6. Scenario model as the primary design pressure

The workflow should use a compact set of end-to-end scenarios as the main pressure on the system model.

These scenarios should be RAG-specific. They are not generic user stories. They should describe evidence-seeking behaviors that force the system to reveal whether the current model is sufficient.

### 6.1 Scenario categories

The initial taxonomy should include at least the following classes.

#### Direct factual lookup
A user asks for a fact that is explicitly present in one passage or one tightly bounded region of a document.

This pressures:

- passage quality,
- anchor correctness,
- top-k retrieval precision,
- answer citation behavior.

#### Section-scoped explanation
A user asks for an explanation that requires a locally coherent reading of a section, not just one sentence.

This pressures:

- section hierarchy,
- neighbor expansion,
- context assembly,
- citation granularity.

#### Multi-passage synthesis within one document
A user asks a question that requires combining several non-adjacent but related passages from the same source.

This pressures:

- retrieval recall,
- ordering policy,
- evidence-set assembly,
- claim aggregation.

#### Cross-document synthesis
A user asks a question whose support is distributed across multiple documents.

This pressures:

- corpus-level retrieval,
- document identity discipline,
- citation grouping,
- answer scoping,
- conflict handling.

#### Source navigation / citation resolution
A user wants to inspect the source behind the answer.

This pressures:

- anchorability,
- citation resolution,
- stable document-to-anchor linkage,
- trustworthy answer presentation.

#### Insufficient-evidence case
A user asks for something that the corpus does not support.

This pressures:

- abstention logic,
- unsupported-claim prevention,
- scope-narrowing behavior,
- retrieval failure interpretation.

#### Low-quality or malformed source case
The corpus contains a document with damaged structure, ambiguous sections, OCR-like artifacts, malformed tables, or broken layout.

This pressures:

- parser robustness,
- representation quality boundaries,
- fallback behavior,
- failure containment.

### 6.2 Scenario structure

Each scenario should specify:

- the corpus condition,
- the information need,
- the evidence pattern required to answer it,
- the expected answer behavior,
- the expected failure behavior if support is not found.

### 6.3 Why scenarios come before domains

Scenarios express the full request lifecycle. Domains do not.

A domain-only workflow often causes each subsystem to optimize for its local success condition while the end-to-end system still fails. By using scenarios first, delivery stays centered on observable product behavior and evidence flow.

---

## 7. Evidence model

The workflow should elevate evidence to a first-class concept.

This is one of the most important changes in the rewrite. Many weak RAG workflows speak about retrieval and citations without explicitly defining what evidence is, what counts as support, and how evidence composes into answerable claims.

### 7.1 What counts as evidence

Evidence is any source-linked representation that can legitimately support a user-visible claim.

In the first version, the main evidence objects are likely:

- passages,
- section context metadata,
- table-preserving fragments,
- code-preserving fragments,
- possibly derived structured evidence such as graph edges when those remain anchored.

### 7.2 Evidence properties

An evidence unit should have, conceptually, the following properties:

- stable identity within a document version,
- link to document identity,
- anchor or anchor set,
- structural position,
- local text or renderable content,
- compatibility with retrieval and citation.

### 7.3 Evidence sufficiency

The model should distinguish three states:

- **sufficient evidence**: the available evidence supports the claim,
- **partial evidence**: the available evidence suggests an answer but does not justify a confident claim,
- **insufficient evidence**: the corpus does not support the claim.

Without this distinction, the generator becomes the de facto judge of sufficiency, which is unsafe.

### 7.4 Evidence sets and claim support

A claim may require one evidence unit or several. The workflow should therefore model **evidence sets** rather than assuming one-claim-to-one-passage mapping.

Examples:

- a factual lookup may need one passage,
- a procedural explanation may require a section-level span,
- a synthesis answer may require several passages across one or more documents.

### 7.5 Evidence and delivery

Evidence modeling is not just a semantic exercise. It directly drives:

- retrieval-unit design,
- citation rules,
- context assembly policy,
- abstention behavior,
- test design,
- prototype validation criteria.

If the evidence model is weak, every downstream component becomes ambiguous.

---

## 8. Retrieval-unit model

The workflow should explicitly define the retrieval-unit model because retrieval-unit design is one of the strongest determinants of downstream answer quality.

### 8.1 Why retrieval units matter

A retrieval unit is not merely an embedding chunk. It is the main boundary between source representation and evidence retrieval.

If the unit is too large, retrieval precision degrades and context becomes noisy.

If the unit is too small, local coherence, coreference, and evidence completeness break down.

If the unit ignores structure, anchors become unreliable and citations lose meaning.

### 8.2 Recommended retrieval-unit hierarchy

The workflow should assume a hierarchy at least of the form:

`DOCUMENT -> SECTION -> PASSAGE`

This hierarchy supports several behaviors that flat chunking does not support well:

- structure-preserving segmentation,
- local neighbor expansion,
- section-aware assembly,
- stable citation surfaces,
- bounded churn under small edits.

### 8.3 Relationship among sections, passages, and neighbors

The model should clearly distinguish:

- **section** as the semantic and structural container,
- **passage** as the default retrieval unit,
- **neighbors** as expansion candidates for context coherence,
- **section headers or metadata** as optional context scaffolding.

This prevents a common modeling collapse where all source fragments are treated as interchangeable text blobs.

### 8.4 Retrieval-unit policy questions

The workflow should require explicit answers to the following modeling questions:

- What is the default retrievable unit?
- When can a section itself be retrieved?
- How are tables and code blocks represented without semantic damage?
- How is adjacency represented for neighbor expansion?
- How are ordinals or order semantics preserved?
- How is overlap managed?
- What causes a retrieval unit boundary to change across document versions?

### 8.5 Consequence for delivery

The retrieval-unit model should be fixed early enough to shape contracts and evaluations, but not so rigidly that it blocks prototype-driven refinement. The right approach is to lock the minimal semantics of units and anchors while allowing implementation details to evolve.

---

## 9. Shared invariants of the system

The workflow should define the non-negotiable invariants that every domain must preserve.

These invariants are the durable laws of the system. They should survive rewrites, framework changes, and internal reorganization.

### 9.1 Stable identity

Documents must have stable identity across re-ingestion.

Retrieval units should have stable identity within a document version, and changes across versions should remain traceable with bounded churn where feasible.

### 9.2 Anchorability

Every evidence-bearing object must map back to a source location. If an answer can cite it, the system must be able to resolve it.

### 9.3 Hierarchical integrity

Where a hierarchy is defined, it must remain structurally valid. Parent-child relationships, ordinals, and paths must not drift into ambiguity.

### 9.4 Deterministic behavior for identical inputs

Given identical corpus content, configuration, and processing rules, the representation layer should behave deterministically where feasible and otherwise remain structurally stable enough to support reproducibility, regression analysis, and stable evaluation.

If some source classes require probabilistic or model-based extraction, the workflow should pin the extraction configuration, capture extraction provenance, and define acceptable structural variance rather than pretending exact output determinism is always achievable.

### 9.5 Deterministic ordering semantics

Retrieval and context assembly should preserve explicit ordering rules. Ties and deduplication should not be left to accidental runtime behavior.

### 9.6 Explicit unsupported-evidence behavior

The system must not silently convert weak evidence into confident claims. Unsupported-evidence behavior must be part of the contract.

### 9.7 Evidence-to-claim traceability

Claims shown to users must remain auditable against retrieved evidence. Even if the interface does not expose claim-level metadata initially, the conceptual model should preserve the mapping.

### 9.8 Why invariants come before architecture

A team can rewrite modules, merge services, or replace libraries without violating the workflow if these invariants remain intact. That is the correct definition of architectural freedom at this stage.

---

## 10. Bounded context map for the RAG system

Only after the conceptual model, quality model, evidence model, retrieval-unit model, and invariants are explicit should the workflow define bounded contexts.

The goal of bounded context mapping here is not to create a microservice plan. It is to partition responsibilities so that each domain has a coherent semantic role and a clear obligation to preserve specific invariants.

### 10.1 Candidate bounded contexts

A reasonable first map is:

#### Source Acquisition / Corpus Intake
Responsible for fetching source artifacts and establishing source identity and version inputs.

#### Structural Parsing & Distillation
Responsible for canonicalizing documents into structured representations and producing anchorable structure.

#### Segmentation / Retrieval Unit Construction
Responsible for turning structure into retrievable units without breaking semantic coherence or traceability.

#### Indexing & Retrieval
Responsible for making evidence discoverable at query time.

#### Context Assembly
Responsible for transforming retrieved evidence into an ordered, budget-constrained context window suitable for generation.

#### Answer Generation & Citation Rendering
Responsible for producing grounded answer text and exposing support through citations or abstention.

#### Evaluation / Verification
Responsible for checking whether the system preserves the intended semantics and quality thresholds across layers.

### 10.2 How to define each bounded context

Each bounded context should be defined by:

- what semantic responsibility it owns,
- what concepts it consumes,
- what concepts it emits,
- which invariants it must preserve,
- what it is explicitly not responsible for.

### 10.3 What bounded contexts are not

They are not yet deployment units.
They are not automatically teams.
They are not necessarily packages.
They are not permission to redefine shared concepts locally.

At this stage they are modeling boundaries that help delivery and reasoning.

### 10.4 Why this matters for workflow

Without bounded contexts, the model is too abstract to drive engineering.
With premature bounded contexts, the architecture ossifies before the evidence model is tested.

The workflow should therefore introduce domains only at the point where they clarify responsibility without taking over the design.

---

## 11. Context mapping and shared kernel

Once bounded contexts exist, the workflow must distinguish global shared concepts from domain-local models.

### 11.1 Shared kernel

The shared kernel should contain the concepts that must remain globally stable across domains.

At minimum this should include concepts like:

- `doc_id`,
- `doc_version`,
- `segment_id`,
- `anchor_ref`,
- section path or equivalent hierarchy locator,
- ordering semantics,
- evidence support semantics,
- citation semantics.

These should not be reinterpreted independently by each domain.

### 11.2 Domain-local models

Each bounded context may still have local representations, internal helper types, and implementation-specific abstractions. Those are expected.

The rule is that local freedom cannot break shared kernel meaning.

### 11.3 Why this is critical in RAG systems

RAG systems are especially vulnerable to subtle semantic drift between domains.

Examples:

- the parser and segmenter disagree on anchor semantics,
- retrieval uses a unit identity that citation rendering cannot resolve,
- context assembly drops ordering assumptions needed by answer rendering,
- evaluation measures a different notion of evidence than generation uses.

A clear shared kernel prevents these mismatches.

---

## 12. RAG failure taxonomy

The workflow should explicitly model failure as part of the system domain.

A strong RAG workflow does not only describe the success path. It also names the ways the system can fail, because those failures often determine both architecture and evaluation priorities.

### 12.1 Representation failures

Examples:

- structure tree missing meaningful hierarchy,
- list or table semantics destroyed,
- code blocks split incorrectly,
- anchors misaligned or non-resolvable,
- version churn too high after small edits.

### 12.2 Segmentation failures

Examples:

- semantically mixed passages,
- passages too small to preserve local meaning,
- broken discourse boundaries,
- table/header separation,
- loss of section relationship.

### 12.3 Retrieval failures

Examples:

- relevant evidence not retrieved,
- partial evidence outranking complete support,
- retrieval dominated by noisy long passages,
- rank instability under equivalent queries.

### 12.4 Context assembly failures

Examples:

- redundant overlapping passages consuming budget,
- missing neighbors where local coherence is needed,
- unstable ordering,
- over-concentration on one section or one document,
- truncation removing crucial support.

### 12.5 Answering failures

Examples:

- unsupported claims,
- incorrect synthesis across evidence units,
- citation attached to the wrong anchor,
- overconfident interpretation of ambiguous evidence,
- answering instead of abstaining.

### 12.6 Why the taxonomy matters

The failure taxonomy gives the workflow a structured way to:

- derive evaluations,
- compare prototype variants,
- interpret regressions,
- decide which boundaries are actually under pressure.

It also prevents vague discussions such as "quality feels worse" when the true failure is, for example, evidence fragmentation or anchor mismatch.

---

## 13. Domain modeling outputs that should drive implementation

The workflow should state clearly what comes out of modeling and becomes binding input to engineering.

The outputs are not broad requirements documents. They are the minimal durable products of analysis.

### 13.1 Required modeling outputs

The domain modeling effort should produce at least:

#### Scenario set
A compact but representative set of end-to-end RAG scenarios that pressure the system.

#### Conceptual vocabulary
A stable vocabulary for core objects and relationships.

#### Invariant set
The non-negotiable laws of the system.

#### Evidence model
A definition of evidence units, evidence sets, and support sufficiency.

#### Retrieval-unit model
A definition of document, section, passage, adjacency, and ordering semantics.

#### Bounded context map
A semantic partition of subsystem responsibilities.

#### Shared kernel definition
The globally stable cross-domain concepts.

#### Failure taxonomy
A named set of failure classes the system must detect, prevent, or contain.

#### Evaluation harness and baseline dataset
A concrete question set, representative corpus slice, and scoring mechanism derived from the scenario set and failure taxonomy.

### 13.2 Why these outputs matter more than early architecture diagrams

These outputs are durable because they preserve the system's semantics. Early class diagrams, packages, or service decomposition are rarely durable at this stage.

The workflow should therefore measure modeling success by whether these outputs are clear and usable, not by whether a target architecture has been fully specified.

---

## 14. Integration of domain modeling into delivery

This section is the bridge from conceptual modeling to practical delivery.

The key principle is that **delivery should be driven by the model, and architecture should be driven by evidence from the running system**.

### 14.1 Delivery loop

The core loop should be:

1. define the end-to-end scenarios,
2. define the conceptual objects and evidence semantics,
3. lock the minimum shared invariants and shared kernel,
4. derive the bounded contexts and minimal contracts,
5. implement the evaluation harness and baseline dataset derived from the scenario and failure model,
6. implement a thin integrated prototype,
7. pressure the prototype with the scenario and failure model through the evaluation harness,
8. refine the model where reality disproves assumptions,
9. extract the minimal durable architecture from what held under pressure.

### 14.2 What should be locked before implementation

Before substantial coding begins, the workflow should expect the following to be stable enough:

- core object vocabulary,
- evidence support semantics,
- retrieval-unit semantics,
- anchor and identity semantics,
- bounded context responsibilities at a coarse level,
- major failure classes.

This is enough to prevent accidental drift while still leaving implementation highly flexible.

### 14.3 What should remain intentionally provisional

Before prototype pressure, the workflow should keep the following provisional:

- internal module boundaries,
- framework choices,
- storage layout,
- orchestration details,
- packaging and deployment topology,
- performance optimizations not required by the chosen scenarios.

### 14.4 Why this is superior to architecture-first delivery

Architecture-first delivery optimizes for the shape of the system before the team has enough evidence to know which shape matters.

Model-first delivery optimizes for semantic correctness and uses the prototype to reveal real seams. This is a better fit for an early RAG system where the dominant risk is not that the codebase is inelegant, but that the evidence model and retrieval behavior are wrong.

---

## 15. Prototype as a domain-discovery instrument

The workflow should define the role of the prototype very precisely.

The prototype is not a half-production system to be protected because of sunk cost. It is a controlled instrument for discovering whether the current model is sufficient.

### 15.1 What the prototype should validate

The prototype should help answer questions such as:

- Are the chosen retrieval units actually suitable?
- Are the anchor semantics sufficient for citation?
- Do the bounded contexts correspond to real responsibility boundaries?
- Is the shared kernel too thin or too broad?
- Which failure classes dominate in practice?
- Which scenario classes remain hard even with the current model?

### 15.2 What the prototype should not optimize for

The prototype should not prematurely optimize for:

- polished production hardening,
- exhaustive modularization,
- final deployment topology,
- long-term operability concerns that are not yet under pressure,
- abstract extensibility for hypothetical future needs.

### 15.3 Why this matters

If the workflow does not define the prototype explicitly as a discovery tool, teams tend to over-interpret prototype code as architecture. That makes later correction expensive and politically harder than it should be.

The workflow should instead treat prototype code as disposable and prototype findings as durable.

---

## 16. Architecture extraction criteria

The workflow should end its conceptual core by stating how architectural commitment is earned.

Architecture should be extracted from validated behavior, not asserted in advance.

### 16.1 What qualifies for promotion into durable architecture

A boundary, contract, or abstraction should be promoted only if it has demonstrated one or more of the following under scenario and failure pressure:

- it preserves essential invariants,
- it cleanly separates responsibilities,
- it stabilizes integration behavior,
- it reduces a recurring failure mode,
- it remains intelligible across the document and query lifecycles,
- it continues to hold across multiple realistic scenarios.

### 16.2 What should not be promoted yet

Do not promote a pattern into architecture merely because:

- it emerged in the first prototype,
- it makes the current code easier to organize,
- it looks consistent with conventional service decomposition,
- it anticipates a scale or feature set not yet under pressure.

### 16.3 Outcome of the workflow

The intended outcome of this workflow is not just a running prototype.

The intended outcome is:

- a validated conceptual model,
- a tested evidence model,
- a stable set of invariants,
- a clarified bounded context map,
- and a minimally sufficient architecture grounded in actual system behavior.

That is the correct foundation for later production hardening and more mature workflow policy.

---

## Closing thesis

This workflow rewrite changes the center of gravity of delivery.

We do not begin by decomposing implementation work or by designing the target architecture in detail. We begin by defining what a document-grounded RAG system is: what its objects are, how evidence flows through it, what retrieval units mean, what failures matter, and which invariants must survive any rewrite.

Domains are derived from that model, not substituted for it.

Implementation is then used as a fast and disposable instrument to pressure the model. The prototype exists to expose which boundaries are real and which abstractions are accidental. Only after that pressure do we extract the minimal durable architecture.

That is the right workflow for an early-stage RAG system where code is cheap, uncertainty is high, and the main engineering risk is not writing the wrong modules but misunderstanding the semantics that the system must preserve.
