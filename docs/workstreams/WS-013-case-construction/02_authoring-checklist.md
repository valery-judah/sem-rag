Yes. For LLM-generated synthetic cases, I would **not** use the rubric’s run-level record as the generation target. That record is for an actual model run under evaluation. The better pattern is:

1. prepare a **question-level case file**, based on the rubric schema, and
2. add an **answer key / judgment key** that your evaluator can use later.

That fits your docs cleanly. The rubric already separates:

* **question-level record**: question, class, support state, provenance expectation, gold sources, notes, and
* **run-level record**: model answer, returned sources, rubric judgments, failure labels. 

So for synthetic data generation, the LLM should generate the **question-level part plus oracle metadata**, not the run-level scored outcome.

## What I would build first

Since you want to start with 2–3 Markdown sources, I would begin with only one scenario family:

**supported lookup**

That is the simplest because your rubric defines `SUPPORTED` cases clearly: the corpus contains enough evidence for a direct answer, and correct behavior is to answer directly and cite the relevant section or page.

For Markdown, your support-semantics doc already gives the provenance rule you need: a citation is useful when a reviewer can navigate to the right file and locate the material through stable document structure without excessive searching. 

## The structure I recommend

I would use **one JSONL record per eval case** with three blocks:

* `case_metadata`
* `question_spec`
* `answer_key`

That keeps the file ready for generation, judging, and debugging.

### Recommended case format

```json
{
  "case_id": "lookup_md_001",
  "corpus_id": "corpus_alpha",
  "case_family": "supported_lookup",
  "primary_target_failure": ["A1", "P1", "P2"],
  "source_type": "markdown",

  "question_spec": {
    "question": "What are the deployment prerequisites for service Z?",
    "question_class": "factual_lookup",
    "support_state": "SUPPORTED",
    "minimum_provenance": "document_and_section",
    "user_intent_note": "Direct fact lookup, not synthesis."
  },

  "answer_key": {
    "answer_type": "short_list",
    "canonical_answer": [
      "Service account created",
      "Database migration completed",
      "Feature flag enabled"
    ],
    "acceptable_paraphrases": [
      "A service account must exist",
      "DB migrations must already be applied",
      "The rollout feature flag must be turned on"
    ],
    "must_include": [
      "service account",
      "database migration",
      "feature flag"
    ],
    "must_not_include": [
      "Kubernetes autoscaling enabled"
    ],
    "gold_evidence_set": [
      {
        "doc_id": "deployment_guide",
        "display_name": "Deployment Guide",
        "section_path": ["Service Z", "Prerequisites"]
      }
    ],
    "expected_behavior": "Direct answer with section-level citation.",
    "abstention_expected": false
  },

  "authoring_notes": {
    "difficulty": "easy",
    "paraphrase_level": "medium",
    "single_hop": true
  }
}
```

This is basically the rubric’s question-level schema, extended with an answer key. The rubric already defines `question`, `question_class`, `support_state`, `minimum_provenance`, and `gold_sources`, and the glossary gives you the right term for the evidence side: **gold evidence set**.

## Why this structure works

Because it cleanly separates three things:

### 1. What the case is

That comes from the rubric:

* question,
* question class,
* support state,
* provenance expectation,
* gold sources. 

### 2. What a good answer must contain

This is your answer key:

* canonical answer,
* acceptable paraphrases,
* must-include concepts,
* must-not-include unsupported extras,
* gold evidence set.

This is not explicitly defined as a schema in the docs, but it is the practical extension you need if you want LLM-generated cases to be immediately usable in eval.

### 3. What behavior should happen

This should be explicit:

* direct answer expected,
* abstention expected or not,
* qualification required or not.

That comes directly from support semantics. For `SUPPORTED`, a direct answer is allowed and uncertainty language is not required. For partial or insufficient support, qualification or abstention is required.

## The minimum fields I would require

For your first version, I would make these fields mandatory.

### Case metadata

* `case_id`
* `corpus_id`
* `case_family`
* `primary_target_failure`
* `source_type`

### Question spec

* `question`
* `question_class`
* `support_state`
* `minimum_provenance`

These are directly aligned with the rubric. 

### Answer key

* `canonical_answer`
* `answer_type`
* `must_include`
* `must_not_include`
* `gold_evidence_set`
* `expected_behavior`
* `abstention_expected`

That is the practical eval extension.

## Bucket selection rules

Keep the case-family choice tied to **corpus reality**, not to how qualified the final answer sounds.

* Use `ambiguous_conflict` / `AMBIGUOUS_OR_CONFLICTING` only when the answer must surface materially divergent signals or explicitly source-qualify a real conflict.
* Do **not** put a case in the ambiguous bucket just because the answer is narrow or qualified.
* Direct qualified conclusions such as “no final default was ratified,” “the document does not prove a universal claim,” or “the recommendation remains configurable” belong in `SUPPORTED` when the corpus directly supports that reading.
* When that direct answer is explanatory rather than a short fact lookup, use `supported_localized_explanation`.
* For unsupported requests, keep the natural question shape where possible. Missing values, paths, filenames, counts, or coordinates are usually `factual_lookup`; broader “what decision/result/policy does the file give?” questions are usually `localized_explanation`.
* Reserve `unsupported_scope` / `UNSUPPORTED_QUESTION_TYPE` for scope-boundary requests such as image reading, OCR recovery, or external-web completion.

## Evidence authoring rules

Keep locator metadata and verbatim evidence separate.

* In `cases.jsonl`, `question_spec.gold_sources` should contain only locators such as `doc_id`, `display_name`, and `section_path`.
* Do not place `support_snippet` in case-side `gold_sources`.
* Put verbatim evidence only in `answer_keys.jsonl` under `gold_evidence_set`.
* Every `support_snippet` should be an exact substring of the cited section text.
* Do not shorten evidence with `...` or `…`.
* Preserve Markdown emphasis, bullets, and numbering when those are part of the exact source text.

## What not to generate yet

I would **not** ask the LLM to generate these as primary fields yet:

* `support_alignment`
* `scope_control`
* `provenance_quality`
* `overall_trust_outcome`
* `primary_failure_label`
* `severity`
* `detectability`
* `recoverability`

Those are run-level judgment outputs in the rubric, not authoring-time truth fields.

You can still store **target failure** at authoring time, but that is different from a scored failure label.

## How I would use the LLM

Given 2–3 Markdown files, I would make the LLM generate cases in two passes.

### Pass 1: source grounding pass

For each Markdown file, extract:

* `doc_id`
* `display_name`
* heading hierarchy
* candidate factual statements suitable for lookup
* section paths where each statement is supported

This matters because for Markdown your provenance has to resolve through structure, not page numbers. 

### Pass 2: case generation pass

Generate eval cases only from those extracted factual statements.

For each case, require the model to output:

* one narrow question,
* `question_class = factual_lookup`,
* `support_state = SUPPORTED`,
* one `gold_evidence_set`,
* one canonical answer,
* paraphrase variants,
* must-include / must-not-include constraints.

That keeps the generation anchored to real support instead of inventing attractive but unstable questions.

## A good prompt contract for the LLM

I would constrain the generator with rules like:

* only generate `SUPPORTED` factual lookup questions
* answer must be directly supported by one local section
* do not require synthesis across multiple documents
* do not use tables, images, charts, code execution, or external knowledge
* every case must include a resolvable `section_path`
* every answer key must list unsupported distractors in `must_not_include`
* output strict JSON only

That is consistent with the support rules and with your MVP scope boundaries. Unsupported question types should not be silently turned into supported cases.

## What “ready to use in eval” should mean

For me, “ready to use” means the case file already contains enough information to support:

### generation-time use

* sampling and filtering
* source-aware prompts
* dataset inspection

### run-time use

* sending the question to the RAG system

### eval-time use

* checking whether the answer included the required facts
* checking whether unsupported extras were added
* checking whether the returned citation maps to the gold evidence set or at least the right local section

That last point matters because your docs treat provenance as part of the trust contract, not a side metric. Weak or false provenance is a failure even when answer text is plausible.

## My recommended first version

For your first synthetic dataset, I would keep it very tight:

* only Markdown
* only `supported_lookup`
* only `factual_lookup`
* only section-level provenance
* one source section per case
* short answers only: scalar, short phrase, or short list
* one primary target failure set per case: usually `["A1","P1","P2"]`, optionally `["U1"]`

That will give you a dataset that is easy to generate and easy to judge.

## Phase-zero storage layout

For phase zero, keep the **question / answer-key split**, but store each authored slice in its own folder under `evals/cases/sets/`.

Use this shape:

* `evals/cases/cases.schema.json`
* `evals/cases/answer_keys.schema.json`
* `evals/cases/sets/<set_id>/cases.jsonl`
* `evals/cases/sets/<set_id>/answer_keys.jsonl`

Where:

* the top-level schema files are shared across authored sets,
* each `<set_id>` folder is one bounded case slice,
* the folder name should say both the scenario family and the source bundle, for example `supported_lookup_research_1`.

Treat those shared schema files as the **authoring superset** aligned with the case matrix, not as the contract for only one scenario family. A specific set folder may intentionally use only a narrow subset of the allowed enums.

### `sets/<set_id>/cases.jsonl`

Contains:

* case metadata
* question spec
* gold evidence set
* provenance expectation

### `sets/<set_id>/answer_keys.jsonl`

Contains:

* `case_id`
* canonical answer
* acceptable paraphrases
* must include
* must not include
* expected behavior
* abstention expectation

This keeps authored sets easy to inspect and extend during phase zero, while still preserving the split between runnable questions and oracle metadata.

The important boundary is:

* shared schemas define the matrix-ready enum and field envelope
* set-specific checks enforce narrower slice rules for a given authored batch

## Bottom line

For LLM-generated synthetic cases, I would use this authoring model:

**question-level eval case + answer key**, not question-level + fake run-level score.

That aligns with the rubric’s separation between:

* what the corpus supports, and
* how a particular system run behaved.

The simplest useful MVP format inside a set folder is:

```json
{
  "case_id": "...",
  "corpus_id": "...",
  "case_family": "supported_lookup",
  "question_spec": {
    "question": "...",
    "question_class": "factual_lookup",
    "support_state": "SUPPORTED",
    "minimum_provenance": "document_and_section"
  },
  "answer_key": {
    "canonical_answer": "...",
    "must_include": ["..."],
    "must_not_include": ["..."],
    "gold_evidence_set": [{ "doc_id": "...", "section_path": ["..."] }],
    "expected_behavior": "Direct answer with section citation.",
    "abstention_expected": false
  }
}
```

That is the format I would start with.

I can next draft a strict JSON schema for this, plus an LLM prompt that generates cases from your Markdown sources.
