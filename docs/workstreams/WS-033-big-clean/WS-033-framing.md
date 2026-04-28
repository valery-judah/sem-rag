# Framing

## Problem
The repo now has enough real product and runtime capability that the main problem is no longer "is there a system here?" The problem is that the story of the system is still harder to understand than it should be.

`doc_forge` already has a bounded MVP definition, a verified current-state architecture doc, a verified stable localhost API contract, a durable runbook, implemented lifecycle processing through `READY`, and an executable query pipeline through answer generation plus citation rendering. It also has a growing set of WS-033 notes that sharpen the trust contract, support-state model, and evaluation direction.

What it does not yet have is one coherent review artifact that starts from the existing system as it is today, walks the reader through the product/runtime shape end to end, and then explains why the cleanup work matters. Current truth is split across evergreen docs, workstream notes, and package seams. That makes "what exists now" harder to reconstruct than necessary, especially for someone trying to decide what should be promoted, consolidated, or deleted next.

WS-033 exists to produce that review baseline before more cleanup work spreads across additional notes.

## Scope
- Rewrite this framing artifact as a current-state review of the existing system and its documentation.
- Ground the review in implemented code plus canonical evergreen docs.
- Explain the system from the top down: product promise, architecture, stable public interface, operations, lifecycle flow, and query flow.
- Capture the specific reasons the system story still feels fragmented and what decisions WS-033 must drive next.
- Define the cleanup direction for narrative coherence and documentation authority without changing runtime behavior.

## Constraints
- Evergreen docs remain canonical. This workstream may synthesize and critique, but it does not override `docs/evergreen/`.
- No runtime API, schema, or type changes are part of this framing artifact.
- The stable public contract remains the localhost FastAPI route set documented in `docs/evergreen/api-contracts.md`.
- Internal lifecycle stages, query stages, citations, traces, and storage seams may be described as implemented architecture, but they are not promoted here into public Python APIs.
- Claims in this document should be supportable from either current code or canonical evergreen docs, not from WS-033 notes alone.

## Input context
- paths:
  - `docs/evergreen/mvp.md`
  - `docs/evergreen/architecture.md`
  - `docs/evergreen/api-contracts.md`
  - `docs/evergreen/runbook.md`
  - `src/doc_forge/app/api.py`
  - `src/doc_forge/app/routers/documents.py`
  - `src/doc_forge/app/routers/queries.py`
  - `src/doc_forge/runtime.py`
  - `src/doc_forge/query/service.py`
  - `docs/workstreams/WS-033-big-clean/one-user-story-design-driver.md`
  - `docs/workstreams/WS-033-big-clean/mvp-design-input-minimal.md`
  - `docs/workstreams/WS-033-big-clean/first-tier-failures.md`
  - `docs/workstreams/WS-033-big-clean/eval-support-semantics.md`
- read first:
  1. evergreen docs for canonical product, architecture, contract, and operations truth
  2. current FastAPI/runtime/query code for implemented behavior
  3. WS-033 notes as secondary synthesis material, not as current-state authority

## Key decisions
- Which WS-033 ideas should be promoted into evergreen docs versus kept as workstream-local design material.
- Whether MVP trust-contract language, support-state semantics, and failure framing should be consolidated into a smaller evergreen set.
- How much of the existing WS-033 note set should be merged, reduced, or deleted after the review baseline exists.
- Whether the cleanup goal is only better narrative coherence or also stronger authority and boundary simplification across the doc set.

## Expected outputs
- One current-state review baseline in this framing doc.
- A top-down explanation of the existing system that a new implementer can read before diving into the rest of WS-033.
- A prioritized cleanup map for docs and, if needed, adjacent architecture wording.
- A concrete list of candidate promotions, consolidations, and deletions across the WS-033 note set.

## Exit criteria
- A new implementer can understand the current product/runtime/docs story from this document without re-reading the full WS-033 folder.
- The document clearly separates current truth, identified fragmentation, and proposed cleanup direction.
- The system walkthrough does not present planned capabilities as already implemented.
- The stable API boundary is described consistently with `docs/evergreen/api-contracts.md` and the mounted router shape.
- The next execution pass can use this file as the rationale baseline for WS-033 without rediscovering the same context.

## Objective
Establish a decision-quality framing document that starts from the existing system, explains what is already true, and uses that review to justify the next cleanup pass across docs, workstream notes, and adjacent architecture language.

## Non-goals
- Changing the runtime, routes, persistence model, or query behavior in this framing pass.
- Replacing evergreen docs with this workstream artifact.
- Rewriting every WS-033 note immediately; this framing pass should first define which notes deserve promotion, consolidation, or retirement.
- Treating workstream design language as current implementation truth without code or evergreen support.

## Current system from the start
The current system is a local document question-answering service over a bounded corpus of user-uploaded text-based PDFs and Markdown files. The MVP promise is straightforward: ingest a mixed-format corpus, let a user ask a natural-language question, return a source-grounded answer when the corpus supports one, and make the supporting evidence inspectable. The same product definition also sets the scope boundary: OCR-heavy scans, figure-first and table-first reasoning, and external-world answering remain outside the MVP.

The runtime shape is intentionally simple. Today the system is one FastAPI application plus one worker-driven document lifecycle, one primary relational metadata store, filesystem-backed artifact storage, and an internal query runtime inside the same service boundary. Docker-backed local operation can add host-native Ollama generation on Apple Silicon without changing that core topology, and local observability runs can add a separate Compose stack for query/eval metadata and JSON log browsing.

The stable public interface is the localhost FastAPI API started by `uv run poe run-api`. The stable route set currently includes:

- `GET /healthz`
- `GET /readyz`
- `POST /documents`
- `DELETE /documents/{doc_id}`
- `GET /documents/{doc_id}`
- `GET /documents/{doc_id}/status`
- `GET /documents/{doc_id}/artifacts`
- `POST /documents/{doc_id}/retry`
- `POST /queries`
- `GET /queries/{query_id}`
- `GET /queries/{query_id}/trace`
- `GET /queries/{query_id}/citations`

Optional `/docs` and `/openapi.json` exposure is runtime-configured and broader than the stable public contract. The mounted app also exposes `POST /retrieval/query` and `POST /internal/run-next-job`, but those are runtime-visible internal routes rather than part of the stable contract.

Operationally, the repo already has a durable run path:

- `uv sync` for environment setup
- `uv run poe run-api` for the local HTTP service
- `uv run poe run-worker` for the lifecycle worker
- `make docker-up-build` for the local Docker stack
- `make observability-up-build` and `uv run poe observability-loader-scan` for the separate observability flow
- `uv run poe collect-query-context <query_id>` and `uv run poe show-query-context <query_id>` for query bundle review

From the document side, the current implementation already supports a real lifecycle. `POST /documents` accepts PDF and Markdown uploads, registers them, stores metadata and raw artifacts, and queues the document into the worker-driven pipeline. From there the lifecycle advances through extraction, normalization, section recovery, chunking, indexing, and readiness checks until the document becomes `READY`. Only `READY` documents enter the query-facing corpus.

From the query side, the current implementation already supports a full execution path rather than a retrieval-only prototype. `POST /queries` creates a persisted query run, captures a stable snapshot of eligible `READY` documents, interprets the question, performs dense retrieval, selects evidence, assembles context, assesses support, chooses an answer mode, generates an answer draft, renders citations, persists answer artifacts, and stores stage traces for review. The review surface then exposes the run summary, trace chain, and citation bundle through the stable query routes.

This means the repo has already earned more than an ingestion skeleton or early-stage RAG spike. It has a real local service shape, a stable HTTP contract, a lifecycle boundary, a query boundary, persisted review artifacts, and an operations story. That is the baseline WS-033 should now review and clean up around.

## What is already good
- The repo has a clear product north star in `docs/evergreen/mvp.md`: bounded corpus QA over text-based PDF and Markdown with inspectable evidence and explicit scope limits.
- The repo has a verified current-state architecture doc in `docs/evergreen/architecture.md` that describes topology, bounded contexts, earned seams, and the current gap to the MVP.
- The repo has a verified stable localhost API contract in `docs/evergreen/api-contracts.md`, including a clear split between stable routes and runtime-exposed non-public routes.
- The lifecycle side is materially real, not aspirational: document registration, worker orchestration, stage progression, artifact storage, indexing, and readiness gating all exist in code.
- The query side is materially real, not aspirational: snapshot capture, interpretation, retrieval, selection, context assembly, support assessment, answer-mode selection, answer generation, citation rendering, answer persistence, and trace persistence all exist in code.
- The repo has a usable local operations surface through the runbook, Docker wrappers, and query-context tooling.
- The docs system already has a credible authority model: evergreen for durable truth, workstreams for time-scoped investigation, ADRs for long-lived decisions.

## Where the system story is still fragmented
The fragmentation problem is no longer about missing all documentation. It is about the lack of one clear path through what already exists.

First, current truth is distributed across several layers with different authority:

- evergreen docs define the durable product, architecture, contract, and operations baseline;
- code defines the actual mounted routes, lifecycle behavior, and query-stage execution;
- WS-033 notes define sharper trust, support, and evaluation language, but mostly as parallel drafts rather than as one promoted story.

Second, some concepts now appear in multiple places with different roles. Product trust, support-state behavior, failure language, and evaluation direction are being refined in WS-033 notes while related scope and behavior language already exists in evergreen docs. Without consolidation, readers have to infer which document is explanatory, which is normative, and which is only a design experiment.

Third, the workstream folder already contains useful reframings:

- one design-driving user story for the MVP trust contract,
- a minimal failure-first design input,
- a first-tier failure set,
- a support-semantics draft,
- a case-matrix direction.

Those notes are useful, but they are still easier to read as isolated arguments than as one review of the current system. The repo therefore lacks a baseline document that says: this is the system today, this is what is already strong, this is where the narrative and authority lines still blur, and this is what cleanup should now resolve.

Fourth, the cleanup risk is now editorial and architectural at the same time. If WS-033 only adds more notes, the system story gets richer but harder to navigate. If WS-033 promotes too much too quickly, it risks turning workstream hypotheses into evergreen truth before those decisions are actually settled. The workstream needs a review baseline that can separate implemented fact from promotion candidates.

## Relevant context
- components:
  - FastAPI app assembly and route mounting
  - worker-driven document lifecycle and readiness gate
  - query runtime with persisted runs, traces, and citations
  - evergreen documentation authority system
  - WS-033 design notes on trust, support, and evaluation
- observed current-state anchors:
  - `src/doc_forge/app/api.py` mounts system, documents, queries, and internal routers into one FastAPI app.
  - `src/doc_forge/app/routers/documents.py` exposes upload, delete, detail, status, artifact, and retry routes for documents.
  - `src/doc_forge/app/routers/queries.py` exposes query submission plus summary, trace, and citations review routes.
  - `src/doc_forge/runtime.py` exposes container-friendly `api`, `worker`, and `migrate` runtime commands.
  - `src/doc_forge/query/service.py` executes the persisted query flow through interpretation, retrieval, selection, context assembly, support assessment, answer-mode selection, generation, citation rendering, and trace persistence.
- documentation strengths:
  - `docs/evergreen/mvp.md` gives the product boundary.
  - `docs/evergreen/architecture.md` gives the current implemented shape and gap to MVP.
  - `docs/evergreen/api-contracts.md` gives the stable HTTP boundary.
  - `docs/evergreen/runbook.md` gives the operational path.
- documentation pressure points:
  - support and trust semantics are becoming sharper in WS-033 than in the evergreen baseline.
  - some of the strongest explanatory material is still workstream-local rather than promoted or consolidated.
  - the repo still lacks one top-down "start here to understand the existing system" review artifact inside WS-033 itself.

## Detached-work handoff
- Treat this framing doc as the current rationale baseline for WS-033 execution.
- Start future WS-033 execution from the existing-system review above rather than from any single downstream note.
- Do not re-open whether the repo already has a meaningful current system. That is established here: the question is how to narrate, consolidate, and govern it more cleanly.
- Expected execution slices:
  - decide which WS-033 notes should be promoted into evergreen docs
  - reduce duplicated trust/support/evaluation language across workstream artifacts
  - define which notes remain design material and which should be retired after promotion
  - tighten any adjacent architecture wording that makes the current system story harder to follow
- Preserve the distinction between:
  - current implemented truth
  - workstream-local design sharpening
  - final evergreen promotions still requiring explicit decisions

## Workflow steps
1. Use this framing document as the review-first baseline for WS-033.
2. Inventory the WS-033 note set against the evergreen canon and label each note as:
   - promote
   - consolidate
   - keep workstream-local
   - retire after extraction
3. Decide whether trust/support semantics should become a smaller evergreen package or remain partially workstream-local during further design.
4. Execute the chosen cleanup path and record the resulting doc moves, promotions, and deletions back into the workstream.

## Validation and Definition of Done
- Every substantive current-state claim in this document should be traceable to either evergreen docs or current code.
- Stable-route language should remain consistent with `docs/evergreen/api-contracts.md` and current mounted routers.
- The lifecycle and query walkthrough should remain implementation-truthful and should not skip the currently implemented stages.
- The document should clearly distinguish:
  - what the system already is,
  - what is good about it,
  - where the story is fragmented,
  - which cleanup decisions remain open.
- Markdown-only validation is sufficient unless a later edit introduces new commands or runtime claims that need spot verification.

## Linked artifacts
- `docs/evergreen/mvp.md`
- `docs/evergreen/architecture.md`
- `docs/evergreen/api-contracts.md`
- `docs/evergreen/runbook.md`
- `docs/workstreams/WS-033-big-clean/WS-033-workstream.md`
- `docs/workstreams/WS-033-big-clean/one-user-story-design-driver.md`
- `docs/workstreams/WS-033-big-clean/mvp-design-input-minimal.md`
- `docs/workstreams/WS-033-big-clean/first-tier-failures.md`
- `docs/workstreams/WS-033-big-clean/eval-support-semantics.md`
