The current query-lifecycle requirements are directionally correct, but they are structured as a flat backlog rather than as a clean contract.

They already capture the right substance: corpus-bounded intake, intent-sensitive interpretation, evidence-first retrieval over a `DOCUMENT -> SECTION -> PASSAGE` hierarchy, explicit context assembly, grounded answering, inspectable citations, abstention, deterministic ordering, layered failure handling, and scenario-based validation.   

The structural problem is that the document mixes five different kinds of thing into one list: conceptual semantics, runtime requirements, cross-cutting invariants, validation obligations, and staged delivery. That is misaligned with the workflow, which explicitly says the order should be conceptual vocabulary, lifecycles, invariants, evidence semantics, bounded contexts, then implementation. 

There are also two design gaps.

First, support-state judgment is still implicit. The workflow treats evidence and support semantics as first-class, and warns that without an explicit distinction among sufficient, partial, and insufficient support, the generator becomes the de facto judge of sufficiency, which is unsafe.  

Second, stage contracts are missing. The workflow says bounded contexts should be defined by what they consume, emit, preserve, and are not responsible for, and that the shared kernel should stabilize things like `doc_id`, `segment_id`, `anchor_ref`, ordering semantics, evidence support semantics, and citation semantics. The current requirements do not name those stage outputs explicitly. 

## How I would restructure it

I would turn it into a **contract-first requirements artifact** with six sections.

### 1. Authority and boundary

Keep this short and strict.

Include:

* purpose
* scope / non-scope
* source-of-truth precedence
* statement that this doc does not redefine support semantics, citation semantics, or failure taxonomy

This matters because the vocabulary doc explicitly says evaluation is contract-first and layered, and that workflow language must not broaden MVP scope or evaluation semantics. 

### 2. Query lifecycle contract

This should define the lifecycle as the top-level runtime obligation, not as Requirement 1 among many.

I would write it as:

`Interpret -> Retrieve -> Select -> Assemble Context -> Assess Support -> Decide Answer Mode -> Generate -> Cite`

That is a refinement of the workflow lifecycle, not a replacement. The conceptual workflow can stay `Interpret -> Retrieve -> Select/Rerank -> Assemble Context -> Generate -> Cite or Abstain`, but the requirements doc should make the support decision explicit so abstention and scope narrowing are not hidden inside generation.  

### 3. Stage contracts

Instead of 15 flat requirements, define one requirement block per stage.

For each stage, require four fields:

* consumes
* emits
* preserves
* failure modes

That gives you a proper internal contract surface.

A practical breakdown:

**QL-1 Query boundary and interpretation**
Consumes user question + workspace/corpus boundary.
Emits normalized query intent and retrieval constraints.
Preserves corpus boundedness.
Covers current R2 and R3. 

**QL-2 Evidence retrieval contract**
Consumes interpreted query.
Emits ranked passage candidates with stable provenance identity.
Preserves passage-first retrieval semantics and section context linkage.
Covers current R4 and R5. 

**QL-3 Evidence selection contract**
Consumes raw hits.
Emits evidence sets, not just top-k passages.
Preserves completeness, coherence, deduplication, and multi-document support.
Covers current R6 and R7. 

**QL-4 Context assembly contract**
Consumes selected evidence sets.
Emits ordered, budgeted context artifact.
Preserves ordering semantics, local coherence, and non-loss of crucial support.
Covers current R8. 

**QL-5 Support assessment and answer policy contract**
Consumes context artifact.
Emits support state plus answer mode: direct answer, scoped answer, or abstention.
Preserves canonical sufficient / partial / insufficient semantics.
This should be a new explicit requirement, derived from workflow + support semantics.  

**QL-6 Answer and citation rendering contract**
Consumes answer mode + supportable evidence.
Emits answer artifact + citation artifact, or abstention artifact.
Preserves groundedness, provenance usefulness, and no fabricated support.
Covers current R9, R10, and part of R11-R12.  

### 4. Cross-cutting invariants

Move invariants up, ahead of delivery stages, and make them normative.

These are the right ones to keep:

* corpus-bounded behavior
* passage as default retrievable unit
* recoverable provenance
* deterministic ordering
* evidence-to-answer traceability
* supported answers require inspectable citations
* insufficient-support answers must not fabricate support 

That placement matches the workflow’s ordering and makes the artifact read like a contract rather than a checklist. 

### 5. Failure and validation contract

Do not treat failure handling and validation as the tail end of the doc. Make them a first-class section tied to the lifecycle.

Split this into:

* primary user-visible failure classes
* diagnostic internal failure classes
* validation obligations by stage

That matches both the workflow’s layered quality model and the critical failure spec’s separation between primary trust failures and secondary diagnostic causes.  

Also encode the expected answer policy by support state directly here:

* `SUPPORTED` → answer with inspectable support
* `PARTIALLY_SUPPORTED` → narrow or qualify
* `UNSUPPORTED_IN_CORPUS` → abstain / state lack of support
* `UNSUPPORTED_QUESTION_TYPE` → explicit scope-boundary response
* `AMBIGUOUS_OR_CONFLICTING` → surface ambiguity or qualify by source 

### 6. Delivery plan

Move the current Stage 1–4 material into a separate “delivery plan” section or a separate workstream plan.

Those stages are useful, but they are execution sequencing, not runtime requirements. Right now they dilute the normative part of the artifact. 

## What I would merge, split, and add

I would **merge**:

* R4 + R5 into one “retrieval semantics” requirement
* R6 + R7 into one “evidence selection and evidence-set construction” requirement
* R9 + R10 + R12 into one “answer and provenance contract”
* R14 + R15 into one “failure and validation contract”

I would **split**:

* R11 into two things: support assessment semantics and answer-policy behavior
* “delivery stages” out of the requirements body entirely

I would **add** one missing requirement:

* **explicit support-state decision requirement** between context assembly and answer generation

That addition is the main structural fix.

## A cleaner requirement skeleton

Something like this:

1. Purpose, scope, authority
2. Query lifecycle contract
3. Lifecycle stage requirements

   1. Query boundary and interpretation
   2. Evidence retrieval
   3. Evidence selection and evidence-set construction
   4. Context assembly
   5. Support assessment and answer policy
   6. Answer and citation rendering
4. Cross-cutting invariants
5. Failure and validation contract
6. Delivery sequencing appendix

That structure fits the workflow much better because it keeps semantics first, makes the support decision explicit, and separates runtime contract from rollout mechanics.   

The short version is: the content is mostly right; the shape is wrong. The artifact should read as a **semantic runtime contract with stage outputs and invariants**, not as a single flattened list of everything the team cares about.
