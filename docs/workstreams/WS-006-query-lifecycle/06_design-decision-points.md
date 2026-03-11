Given the current query-lifecycle contract, I would keep query handling in the same local Python/FastAPI codebase as the document lifecycle, with explicit stage outputs and persisted traces, not as a second independent service. That is the cleanest fit with the existing document-lifecycle shape: single-node deployment, internal HTTP API, Postgres, filesystem artifacts, explicit stage boundaries, and inspectable failure surfaces. The existing document design already chose that shape because it keeps lifecycle checkpoints explicit and failures inspectable, while avoiding premature infrastructure complexity.  

The key constraint from the query requirements is that query execution cannot be an opaque “retrieve some chunks, call LLM, done” path. The required runtime path is explicit: `Interpret -> Retrieve -> Select -> Assemble Context -> Assess Support -> Decide Answer Mode -> Generate -> Cite or Abstain`, and the spec explicitly forbids collapsing those decisions into one opaque step.  

So the first design decision is structural:

**1. Do we implement query lifecycle as modules inside one service, or as separate services?**
For MVP: one service, multiple internal components.
Trade-off:

* one service gives lower latency, simpler local Docker deployment, easier debugging, and reuses the same DB/vector/artifact infrastructure;
* separate services improve future scaling and ownership boundaries, but they add coordination cost before the semantics are stable.

I would not split until the query-stage contracts are stable under evaluation pressure. That is consistent with the workflow guidance that semantics and evidence flow matter more than premature service boundaries. 

The main questions I would ask next are these.

**2. What is the query consistency rule against document readiness?**
Should queries search only `READY` documents, or also `INDEXED`, or partially processed documents?
My default: query only `READY`.
Trade-off:

* `READY` only keeps trust semantics clean, because the document design already defines `READY` as “retrievable and inspectable,” not merely processed;
* allowing `INDEXED` or partial docs improves freshness but creates ugly edge cases where retrieval works but citations or provenance do not.  

**3. What latency target are we designing for?**
This determines nearly everything:

* whether reranking can use a cross-encoder,
* whether support assessment can be a separate model call,
* whether citation rendering can be post-processed,
* whether we need caching at retrieval and answer layers.

Without a target, the architecture will drift toward either overbuilt correctness or underbuilt quality.

**4. What is the intended query execution mode: synchronous only, or optionally async?**
My default: synchronous request-response for MVP, with hard timeouts and detailed query traces.
Trade-off:

* synchronous is simpler and aligns with local interactive use;
* async query jobs help with long-running synthesis and evaluation, but add more lifecycle/state machinery.

I would keep async out unless you already know the corpus sizes or models will force it.

**5. How much query interpretation do we want before retrieval?**
The query spec requires preserving distinctions such as factual lookup, section-scoped explanation, synthesis, source navigation, and unsupported question types, but it does not require a heavyweight classifier. 
Decision point:

* heuristic interpretation only,
* lightweight structured LLM interpretation,
* explicit classifier.

My default: structured interpretation step with constrained output schema plus a small amount of deterministic post-processing.
Trade-off:

* heuristics are faster and simpler but brittle;
* LLM interpretation is more flexible but can drift unless tightly schema-constrained.

**6. What retrieval strategy is acceptable for MVP: dense-only, dense+metadata, or hybrid?**
The query contract requires passage-first retrieval with recoverable provenance and explicit retrieval hierarchy, but advanced hybrid retrieval is not mandatory for MVP.  
My default: dense retrieval over passages, plus strict metadata filtering by workspace/document/source type, and optional heading/path features in ranking.
Trade-off:

* dense-only is simplest and probably sufficient initially;
* hybrid will improve exact-term lookup and source navigation, but it increases indexing and ranking complexity.

Since the document lifecycle already persists chunks, headings, page ranges, and provenance-bearing metadata, you have enough structure to start dense-first cleanly.  

**7. Do we add a reranker in MVP?**
The query contract requires explicit selection/reranking that optimizes for support completeness rather than raw retrieval score. 
Decision point:

* no reranker, only retrieval score + heuristics;
* heuristic reranker;
* LLM reranker or cross-encoder reranker.

My default: heuristic reranking first. Use signals like:

* exact heading/path match,
* source-navigation intent,
* support completeness,
* adjacency coherence,
* diversity across documents for synthesis,
* duplicate suppression.

A neural reranker may help later, but for MVP I would first make the logic inspectable.

**8. How do we define an evidence set at runtime?**
This is not a cosmetic question. The spec explicitly says the system must not assume one claim maps to one passage. It must support single-passage answers, passage-plus-neighbor/context answers, and multi-passage multi-document synthesis. 
Decision point:

* evidence set assembled only implicitly in prompt construction,
* evidence set as a first-class runtime object.

I would make `EvidenceSet` explicit. Otherwise support assessment, answer-mode selection, and citation completeness will be hard to test.

**9. How will context assembly enforce budget without breaking support?**
The requirements insist on deterministic ordering, intentional truncation, and auditable assembly.  
Important trade-offs:

* fixed top-k is simple but often wrong for synthesis;
* neighbor expansion improves coherence but increases noise and token cost;
* section header scaffolding improves interpretability but consumes budget.

My default:

* retrieve top N passages,
* form candidate evidence sets,
* expand neighbors only when explanation/synthesis intent requires it,
* always preserve heading/path metadata,
* truncate by dropping lower-value evidence sets, not by clipping inside a selected one.

**10. How is support assessment implemented?**
This is the single most important decision in the query design, because the spec requires an explicit support-assessment stage and forbids leaving it implicit inside generation. 
Options:

* deterministic rules only,
* LLM judge only,
* hybrid.

My default: hybrid.

* deterministic checks for obvious unsupported-question-type and provenance sufficiency;
* structured LLM support assessment over the selected evidence sets;
* conservative downgrade rules after assessment.

This aligns with the requirement that later stages may narrow further but may not widen beyond assessed support. 

**11. How will answer-mode enforcement actually work?**
You need a real guard here, not just a prompt instruction.
Decision point:

* free-form generation with “be careful” prompt,
* structured answer plan first, then rendering,
* one-shot JSON answer with posture fields.

I would do:

1. support assessment emits posture,
2. answer-mode stage emits allowed answer envelope,
3. generation renders only within that envelope.

That is the only clean way to prevent `PARTIALLY_SUPPORTED` from drifting into a full answer and to make `UNSUPPORTED_QUESTION_TYPE` produce an explicit boundary response. 

**12. What citation payload do we expose internally and externally?**
The spec requires source identity plus source-type-appropriate locator, with page for PDFs and stable heading/section locator for Markdown. It also requires preserving multi-source citation bundles for synthesis. 
Decision point:

* expose only minimal citations,
* expose richer internal citation objects and render a minimal subset.

I would keep an internal rich citation object:

* doc_id
* title
* source_type
* chunk_id
* section_id
* heading_path
* page_start/page_end
* snippet
* support_role

Then render only the minimum useful surface in the API/UI. This gives you evaluation leverage without overcommitting the UI.

**13. Do we persist query traces?**
I would ask this early, because without it you will not be able to debug failures across retrieval, support assessment, answer generation, and citation rendering. The query requirements explicitly require layered failure visibility. 
My default: yes, persist query runs in Postgres.
At minimum:

* query_run
* interpreted_query
* retrieved_candidates
* selected_evidence_sets
* assembled_context_manifest
* support_assessment
* answer_mode_decision
* final_answer
* citations
* timings

This is probably the most important compatibility point with the document lifecycle, which already treats persisted stage evidence as the source of truth.

**14. How do we detect ambiguity/conflict across sources?**
The requirements explicitly include `AMBIGUOUS_OR_CONFLICTING` support state and require the system to surface disagreement rather than flatten it. 
Decision point:

* ignore conflict detection in MVP,
* handle only explicit contradictions,
* attempt broader semantic conflict detection.

I would only support explicit or near-explicit contradictions at MVP. Anything broader is expensive and noisy.

**15. What is the policy for out-of-scope question types at query time?**
The spec is clear that unsupported question types must get explicit scope-boundary handling, not a best-effort grounded answer. 
So I would ask:

* do we want strict refusal for figure/table/image-dependent questions,
* or a scoped fallback like “I can only answer from surrounding text”?

This needs to be a product decision, not an incidental model behavior.

**16. What model topology do we accept?**
You need to choose whether to use:

* one LLM for interpretation + support assessment + answering,
* one LLM plus deterministic support rules,
* multiple models.

My default for MVP:

* embedding model for indexing/retrieval,
* one main LLM for interpretation/support/generation via structured subcalls,
* no separate judge model initially.

That keeps the system simpler while preserving the explicit lifecycle stages.

**17. What are the expected corpus sizes and document counts per workspace?**
This is the main operational question because it drives:

* whether Postgres+pgvector is enough,
* whether query-time reranking is affordable,
* how much context assembly can do,
* whether per-workspace filtering remains cheap.

Given the document lifecycle already assumes Postgres plus persisted vectors, I would stay there unless corpus size clearly breaks it. 

**18. How tightly do we couple query logic to document representation?**
The query side depends heavily on document-side guarantees:

* stable `doc_id`,
* section/chunk identity,
* heading path,
* page range or offsets,
* readiness semantics,
* provenance-bearing chunks.  
  The decision here is whether query code reads raw chunk rows directly or goes through a representation adapter.

I would add a thin `EvidenceRepository` / `QueryReadModel` abstraction so query logic does not depend on storage schema details.

My initial defaults, unless you want a different direction, would be:

* one FastAPI service, same codebase as document lifecycle;
* synchronous query path;
* query only against `READY` documents;
* passage-first dense retrieval with metadata filters;
* explicit heuristic selection/reranking;
* explicit `EvidenceSet` objects;
* explicit support assessment and answer-mode stages;
* structured outputs between all query stages;
* persisted query traces in Postgres;
* minimal external citations, richer internal citation objects;
* no microservices, no agent framework, no hidden judge inside generation.
