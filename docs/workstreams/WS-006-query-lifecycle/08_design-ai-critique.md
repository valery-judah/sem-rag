My assessment: **good direction, not implementation-ready as written**. The document gets the system thesis mostly right, but it hardens too many internal decisions too early and introduces at least one contract split that will create drift during implementation.  

What it gets right:

1. It has the correct center of gravity. The design treats the system as evidence-constrained rather than generation-centric, keeps `READY` as the queryability boundary, and makes `Assess Support` plus `Decide Answer Mode` explicit runtime stages instead of burying them inside one prompt. That is aligned with the workflow and the MVP trust contract.   

2. The one-service topology is the right MVP choice. Given the local Docker/FastAPI target, the decision to keep one app, one DB, internal endpoints, and semantic stage boundaries in code rather than in infrastructure is sound. 

3. The design also correctly elevates inspectability. Persisted traces, explicit evidence sets, context manifests, support decisions, and failure labels are consistent with the project’s emphasis on layered quality and failure localization.  

The main problems:

1. **It is over-committed on internal schema and package shape.** The workflow says the order should be product promise → conceptual objects → scenarios → evidence semantics → invariants → failure modes → bounded contexts → contracts → prototype validation. This design already locks in a fairly detailed table model, endpoint set, and package layout. That is an architecture smell for this phase: it reduces room for prototype-driven correction before the real seams are proven.   

2. **The support-state contract is currently split.** `07_design.md` uses five runtime support states: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED_IN_CORPUS`, `UNSUPPORTED_QUESTION_TYPE`, and `AMBIGUOUS_OR_CONFLICTING`. But `eval-support-semantics.md` declares itself the source of truth and defines support-state criteria around three states: sufficient, partial, and insufficient support. That is not a cosmetic mismatch; it affects evaluation, prompting, policy mapping, and stored traces.  

3. **The document mixes support state, answer policy, and diagnostic reason.** The explicit answer-mode stage is a good idea, but the boundaries are still muddy. Right now, unsupported question type and ambiguity/conflict appear inside support assessment, while failures are separately modeled in `query_failure`, and answer posture is separately stored in `query_answer_mode`. Unless you define a strict ownership model, the same semantic decision will be represented in three places. That usually causes drift between traces, evals, and runtime behavior.  

4. **The persistence model is too normalized for MVP.** Persisting all retrieved candidates, evidence-set tables, context-manifest tables, support-assessment tables, answer-mode tables, fragment-link tables, citation tables, and failure tables may be justified later, but as an MVP it is likely more schema than signal. The design is optimizing for maximal inspectability before you know which trace objects actually need first-class querying versus simple JSONB stage snapshots. 

5. **Fragment-level answer linkage overshoots the stated MVP provenance contract.** The MVP only promises coarse, recoverable provenance for PDFs and useful inspection-level source references; it explicitly does not require exact paragraph-level anchoring. A `query_answer_fragment_link` model implies a finer-grained claim/evidence binding than the framing document currently promises.  

6. **The evidence-set builder is slightly too ambitious for Version 1.** The design includes conflict-aware grouping and multi-document synthesis as first-class runtime behavior. But the MVP says synthesis is secondary and does not promise strong compare-and-contrast or exhaustive reconciliation. That means the architecture should support those cases, but it should not assume sophisticated divergence handling as a default capability in the first implementation.  

7. **The query-time consistency boundary is underspecified.** The design says the active corpus must be bounded and known, and only `READY` documents are eligible. That is necessary but incomplete. The document lifecycle has explicit publication/readiness semantics tied to persisted index records and smoke-tested retrieval. The query design should therefore state whether a query reads against a stable corpus snapshot, latest committed `READY` set, or some other publication boundary. Without that, you risk mixed-state reads during ingestion or retry activity.  

8. **Replay and package layout are still premature.** An internal replay capability is useful, but `POST /queries/{query_id}/replay` does not need to be an HTTP surface yet. Likewise, the package layout is already fairly fragmented for a one-service MVP. Both are examples of solving operator ergonomics and code aesthetics before the minimal stable contracts are proven. 

What I would change before approving implementation:

* Collapse the semantic model into three layers:

  * `support_state`: sufficient / partial / insufficient
  * `blocking_or_qualifying_reason`: unsupported question type / ambiguity-conflict / provenance weak / etc.
  * `answer_mode`: direct / narrowed / qualified / abstain
    That removes the current contract overlap and aligns runtime with the evergreen support semantics.  

* Reduce persistence to a smaller core for MVP:

  * `query_run`
  * `query_stage_trace` or stage JSONB snapshots
  * `query_answer`
  * `query_citation`
  * optionally normalized retrieval candidates if eval/debug actually needs SQL-level inspection
    Delay dedicated evidence-set and fragment-link tables until eval pressure proves they are necessary. 

* Make the first implementation policy-default and explicit:

  * top-k retrieval defaults
  * neighbor-expansion rule
  * duplicate suppression rule
  * context budget rule
  * deterministic tie-breaks
  * downgrade-only mapping from support state to answer mode
    The design gestures at these, but it does not yet lock the actual MVP policy.  

* Add a section called something like **Query eval and acceptance contract**. The document already values traces and localized failures, but it should explicitly define stage-level assertions, scenario classes, and what makes a query run trustworthy or not trustworthy under the critical failure taxonomy.  

Bottom line: **retain the architecture thesis, revise the contracts**. I would not throw this draft away. I would mark it as a strong semantic draft that now needs one tightening pass to remove contract overlap, reduce premature schema commitments, and align support-state semantics with the project’s source-of-truth evaluation doc.  

If useful, I can turn this into a line-by-line redline with “keep / change / delete” recommendations against `07_design.md`.
