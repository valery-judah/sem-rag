# Collected Input

## Purpose

This note collects the repo artifacts that currently define result format, answer requirements, citation expectations, and adjacent "writing-style" query cases.

For this workstream, "writing use case" does not appear as a canonical scenario label. The closest existing case families are:

- `supported_localized_explanation`
- `partial_support_answer` with `multi_source_synthesis`

Those are the main places where answer shaping, qualification, and citation behavior are already authored.

## Source-of-truth order

Use this order when docs differ:

1. [MVP](../../evergreen/mvp.md)
2. Evergreen eval docs:
   - [Eval Vocabulary](../../delivery/eval-vocabulary.md)
   - [Eval Support Semantics](../../delivery/eval-support-semantics.md)
   - [Eval Scenario Taxonomy](../../delivery/eval-scenario-taxonomy.md)
   - `eval-failure-taxonomy.md`
3. Stable runtime contract:
   - [API Contracts](../../evergreen/api-contracts.md)
4. Workstream docs and authored eval sets as implementation-facing guidance and examples

This ordering is stated explicitly in [Eval Vocabulary](../../delivery/eval-vocabulary.md).

## Canonical vocabulary to preserve

[Eval Vocabulary](../../delivery/eval-vocabulary.md) matters for this workstream because it fixes the terms that result-use-case docs should use.

Preferred terms:

- `passage` over `chunk` when discussing evaluable retrieval units
- `anchor` for a recoverable source locator
- `citation` for user-visible mapping from answer to evidence
- `support state` over vague labels such as `confidence`
- `supported answer` / `unsupported answer`
- `abstention` or `scope narrowing` over vague fallback language

Definitions that directly affect result-use-case writing:

- `support state`: evaluator judgment about whether corpus evidence warrants the requested answer shape
- `citation`: mapping from an answer or answer fragment to evidence anchors
- `useful citation`: citation a reviewer can realistically follow
- `gold evidence set`: acceptable sufficient evidence for one case
- `answer artifact`: user-visible answer output under evaluation
- `citation artifact`: source references exposed with the answer

Loaded terms that should not be used loosely:

- `grounded`
- `supported`
- `citation`
- `confidence`
- `hallucination`
- `chunk`

## Product and semantic requirements

### MVP product boundary

[MVP](../../evergreen/mvp.md) is the product-level framing:

- answers must be grounded in uploaded PDF and Markdown documents
- users must be able to inspect supporting evidence
- the system must support source-grounded navigation
- when support is weak or missing, the system should narrow scope, abstain, or say so explicitly

### Support-state and citation requirements

[Eval Support Semantics](../../delivery/eval-support-semantics.md) is the main semantic source for result behavior:

- `sufficient support`: direct answer is allowed
- `partial support`: answer should be qualified, narrowed, or explicitly incomplete
- `insufficient support`: abstention is usually preferred

Citation expectations:

- all citations must identify the correct contributing document
- citations must resolve to a useful inspection point
- citations must not fabricate sections, pages, or stronger support than exists
- Markdown citations should use stable heading/section structure
- cross-document answers should expose all materially contributing documents

## Stable runtime result contract

[API Contracts](../../evergreen/api-contracts.md) says these query routes are stable:

- `POST /queries`
- `GET /queries/{query_id}`
- `GET /queries/{query_id}/trace`
- `GET /queries/{query_id}/citations`

It also says request or response shape changes for these stable routes are contract changes.

### Runtime DTOs

The current result payloads are defined in:

- [`src/doc_forge/app/schemas.py`](../../../src/doc_forge/app/schemas.py)
- [`src/doc_forge/app/api_examples.py`](../../../src/doc_forge/app/api_examples.py)

Main response shape for `POST /queries`:

- `query_id`
- `answer`
- `support_state`
- `answer_mode`
- `citations`
- `message`

Important nested structures:

- `AnswerDraft`
  - `answer_text`
  - `visible_limitations`
  - `should_render_citations`
  - `grounded_evidence_set_ids`
  - `generator_version`
- `CitationBundle`
  - `citations`
  - `material_doc_ids`
  - `renderer_version`
- `SourceReference`
  - `doc_id`
  - `document_title`
  - `snippet`
  - optional `section_id`
  - optional `heading_path`
  - optional `page_label`
  - optional `chunk_id`
  - optional `passage_anchor`

Related runtime enums live in [`src/doc_forge/query/contracts.py`](../../../src/doc_forge/query/contracts.py):

- `SupportState`: `sufficient`, `partial`, `insufficient`
- `AnswerMode`: `direct_answer`, `narrowed_answer`, `qualified_answer`, `full_abstention`, `scoped_abstention`, `qualified_uncertainty`

### Runtime enforcement

Citation rendering rules in [`src/doc_forge/query/citation_rendering.py`](../../../src/doc_forge/query/citation_rendering.py):

- non-abstaining answers must not complete without provenance-derived citations
- cited answers require grounded evidence-set ids
- synthesis answers must cite every materially contributing document

Runtime tests that pin the result shape:

- [`tests/app/test_runtime_api.py`](../../../tests/app/test_runtime_api.py)
- [`tests/query/test_query_stage7.py`](../../../tests/query/test_query_stage7.py)

## Eval schemas and authored-set layout

Top-level eval case docs:

- [Eval Case Storage](../../../evals/cases/README.md)
- [Case Schema](../../../evals/cases/cases.schema.json)
- [Answer Key Schema](../../../evals/cases/answer_keys.schema.json)

Shared authored-case rules:

- `cases.schema.json` defines:
  - `case_family`
  - `source_type`
  - `primary_target_failures`
  - `question_spec`
  - `question_class`
  - `support_state`
  - `minimum_provenance`
  - `gold_sources`
- `answer_keys.schema.json` defines:
  - `answer_type`
  - `canonical_answer`
  - `acceptable_paraphrases`
  - `must_include`
  - `must_not_include`
  - `gold_evidence_set`
  - `expected_behavior`
  - `abstention_expected`

Important `expected_behavior` values for result-use-case work:

- `direct_answer_with_section_citation`
- `direct_answer_with_page_citation`
- `qualified_answer_with_citation`
- `abstain_or_state_insufficient_support`
- `surface_ambiguity_with_source_qualification`

## Writing-adjacent authored eval sets

### Supported lookup

Reference docs:

- [Supported case guidance](../WS-013-case-construction/01_supported-cases.md)
- [Authoring checklist](../WS-013-case-construction/02_authoring-checklist.md)

Authored set directory:

- [supported_lookup_research_1](../../../evals/cases/sets/supported_lookup_research_1/)

What it establishes:

- narrow direct-answer questions
- `support_state = SUPPORTED`
- `question_class = factual_lookup`
- section-local grounding for Markdown
- expected behavior: direct answer plus inspectable citation

This set is less about "writing" style, but it is the clearest baseline for direct answer shape and citation minimums.

### Supported localized explanation

This is the closest existing bucket to a writing/explanation result use case.

Reference docs:

- [Case matrix overview](../WS-003-seed-corpus/30_building_case_matrix.md)
- [Authoring checklist](../WS-013-case-construction/02_authoring-checklist.md)

Authored set directory:

- [supported_localized_explanation_cases_rn2](../../../evals/cases/sets/supported_localized_explanation_cases_rn2/)

What it establishes:

- `case_family = supported_localized_explanation`
- `question_class = localized_explanation`
- `support_state = SUPPORTED`
- expected behavior is still `direct_answer_with_section_citation`
- answer must preserve qualification that is directly supported by the corpus, even though the case remains `SUPPORTED`

Typical authored answer traits in this set:

- short explanatory sentence
- explicit scope boundary
- no invented universal claim
- citation set can span multiple sections when needed to keep the explanation accurate

### Partial-support synthesis

This is the closest bucket to a broader writing/synthesis result shape.

Authored set directories:

- [partial_synthesis_research_1](../../../evals/cases/sets/partial_synthesis_research_1/)
- [partial_support_synthesis_cases_rn2](../../../evals/cases/sets/partial_support_synthesis_cases_rn2/)

What these sets establish:

- `case_family = partial_support_answer`
- `question_class = multi_source_synthesis`
- `support_state = PARTIALLY_SUPPORTED`
- expected behavior is `qualified_answer_with_citation`

Typical authored answer traits in this set:

- preserve the supported subclaim
- explicitly reject over-broad conclusions
- carry qualification in the answer text itself
- keep citations attached to the narrower supported reading

## Test-enforced authoring rules

[`tests/test_eval_case_dataset.py`](../../../tests/test_eval_case_dataset.py) is important because it turns some authoring guidance into executable constraints.

It enforces:

- case and answer-key records conform to the shared schemas
- `cases.jsonl` `gold_sources` contain locators, not `support_snippet`
- `answer_keys.jsonl` `gold_evidence_set` contains exact `support_snippet`
- `support_snippet` must be an exact substring of the cited section text
- section paths must resolve to real headings in the source corpus fixture
- set-specific invariants for expected behavior, support state, and target failures

This means the authored sets are not just examples; parts of their format are already locked by tests.

## Persisted review and debugging artifacts

Query result artifacts are also persisted as query-context bundles.

Reference docs:

- [Runbook](../../evergreen/runbook.md)
- [Observability operations](../../evergreen/observability-operations.md)

Implementation:

- [`src/doc_forge/query/context_archive.py`](../../../src/doc_forge/query/context_archive.py)

Bundle root:

- `data/context/queries/<query_id>/`

Core files:

- `manifest.json`
- `summary.json`
- `citations.json`
- `trace.json`
- `replay.json`
- `query-response.json` when final artifacts are available
- `logs/query-events.jsonl`

Optional files:

- `eval-result.json`
- `execution-metadata.json`

These matter for WS-032 because they show the repo already has two different "result" surfaces:

1. live stable HTTP result payloads
2. persisted review/debug result artifacts

## Practical reading order for WS-032

If the goal is to define or compare result use cases, read in this order:

1. [Eval Vocabulary](../../delivery/eval-vocabulary.md)
2. [Eval Support Semantics](../../delivery/eval-support-semantics.md)
3. [MVP](../../evergreen/mvp.md)
4. [API Contracts](../../evergreen/api-contracts.md)
5. [`src/doc_forge/app/schemas.py`](../../../src/doc_forge/app/schemas.py)
6. [supported_localized_explanation_cases_rn2](../../../evals/cases/sets/supported_localized_explanation_cases_rn2/)
7. [partial_synthesis_research_1](../../../evals/cases/sets/partial_synthesis_research_1/)
8. [`tests/test_eval_case_dataset.py`](../../../tests/test_eval_case_dataset.py)

## Working takeaway

Current repo shape suggests three distinct result-use-case patterns already exist:

1. direct supported answer with citation
2. supported explanatory answer that still preserves qualification
3. qualified partial-support answer with citation

If WS-032 is about "writing" results specifically, the strongest current inputs are:

- [supported_localized_explanation_cases_rn2](../../../evals/cases/sets/supported_localized_explanation_cases_rn2/)
- [partial_synthesis_research_1](../../../evals/cases/sets/partial_synthesis_research_1/)
- [Eval Support Semantics](../../delivery/eval-support-semantics.md)
- [Eval Vocabulary](../../delivery/eval-vocabulary.md)
