For `supported lookup`, I would build cases to answer one narrow question:

**Can the system retrieve a clearly supported fact from the corpus, answer directly, and cite it inspectably?** That is exactly the `SUPPORTED` case shape in your rubric: the corpus contains enough evidence for a direct, materially complete answer, and the support should be inspectable in identifiable source locations. 

## What a supported lookup case is

A supported lookup case should usually be:

* `support_state = SUPPORTED`
* `question_class = factual_lookup`
* a **single fact or short bounded set of facts**
* answerable from one local region of one document, or at most a very small number of nearby regions
* not dependent on tables, figures, OCR, or external knowledge
* paired with a provenance expectation that is realistic for the source type. For PDFs, page-level provenance is often enough; for Markdown, section-path provenance is often expected.

This case type is mainly for exposing:

* `A1` wrong abstention,
* `P1` provenance too weak to inspect,
* `P2` incorrect provenance,
  and secondarily `U1` if the model adds unsupported details. That follows directly from the run-level rubric: for `SUPPORTED` cases the correct behavior is a direct answer with inspectable source location, and failure examples include refusing when support exists or adding extra requirements not stated in the corpus.

## The authoring pattern

I would author each supported lookup case with these parts.

### 1. Pick a fact that is explicitly stated

Choose something the corpus says directly and locally. Good lookup targets are things like:

* a requirement,
* a definition,
* a deadline,
* a threshold,
* a named owner,
* a scope statement,
* a listed dependency,
* a version or configuration value,
* a policy rule.

The key is that the answer should be **materially complete from the corpus without synthesis-heavy inference**. That is what qualifies it as `SUPPORTED`.

### 2. Keep the answer shape narrow

The question should ask for a bounded fact, not a broad explanation. Good shapes are:

* “What are the requirements for Z?”
* “What timeout does the doc specify?”
* “Which section defines X?”
* “Who owns Y according to the runbook?”

Bad shapes for supported lookup are:

* open-ended “explain the whole chapter”
* multi-hop comparisons
* requests that likely need synthesis across many documents
* anything where “complete answer” is hard to define.

This follows from the rubric’s distinction between `factual_lookup` and other classes like `localized_explanation` and `multi_source_synthesis`. 

### 3. Make the evidence location crisp

A good supported lookup case should have a gold source that a reviewer can inspect quickly. Your question-level record should include the supporting document and its localizer:

* PDF: document + page, optionally section
* Markdown: document + heading path / section path.

If you cannot point to a clear support location, it is probably not a good supported lookup case.

### 4. Define minimum provenance upfront

This is important. Before running the model, decide what provenance is required for the answer to be inspectable:

* `document_and_page` for most PDF lookup cases
* `document_and_section` for most Markdown lookup cases
* `document_page_and_section_if_available` when both are realistically recoverable.

That matters because supported lookup is not only about answer correctness. It is also about whether the user can get back to the supporting location.

### 5. Write the expected correct behavior

For supported lookup, the correct behavior is simple:

* answer directly,
* do not over-narrow,
* do not abstain,
* cite the relevant document and location.

So each case should have an explicit expected behavior note like:

* “Direct answer with page citation”
* “Direct answer with section-path citation”
* “Answer may paraphrase, but must stay within stated requirement text” 

## A practical template

I would use a question-level template like this:

```json
{
  "query_id": "q_lookup_001",
  "corpus_id": "corpus_alpha",
  "question": "What are the requirements for Z?",
  "question_class": "factual_lookup",
  "support_state": "SUPPORTED",
  "minimum_provenance": "document_and_page",
  "gold_sources": [
    {
      "doc_id": "policy_doc",
      "display_name": "Policy Doc",
      "page_start": 14,
      "page_end": 15,
      "section_path": ["Requirements for Z"]
    }
  ],
  "notes": "Direct lookup; no synthesis needed."
}
```

That structure follows the rubric’s suggested annotation schema.

## Phase-zero storage note

For now, do not place authored case payloads directly at the top of `evals/cases/`.

Use:

* shared schemas at `evals/cases/cases.schema.json` and `evals/cases/answer_keys.schema.json`
* one folder per authored slice under `evals/cases/sets/<set_id>/`
* paired payload files inside each slice folder:
  * `cases.jsonl`
  * `answer_keys.jsonl`

Example:

* `evals/cases/sets/supported_lookup_research_1/cases.jsonl`
* `evals/cases/sets/supported_lookup_research_1/answer_keys.jsonl`

That keeps phase-zero authoring simple without committing to the final dataset packaging scheme yet.

The shared schemas should now be treated as the **matrix-ready superset** for authored cases, not as a lookup-only contract. This note is still about `supported_lookup` authoring specifically, but other set folders may validly use other shared enums such as `supported_source_navigation`, `source_navigation`, or broader support states.

## What to vary across supported lookup cases

You do not want 20 copies of the same easy case. I would vary them across these dimensions:

### Source type

Include both:

* PDF lookup cases
* Markdown lookup cases.

The provenance expectation differs by source type, and your rubric explicitly says citation usefulness should be judged relative to what is realistically recoverable from each.

### Wording difficulty

Include:

* exact lexical match questions,
* paraphrased questions,
* slightly indirect questions where the wording differs from the source text.

This helps test whether retrieval and answering still work when the question is not just copying a heading.

### Localization difficulty

Include:

* one-section obvious answers,
* answers where the right page/section is present but not in the title,
* answers where the fact is in prose rather than a bullet list.

That puts pressure on `P1` and `P2` without turning the case into synthesis.

### Answer cardinality

Include:

* single-value answers,
* short enumerations with 2–4 items,
* short “where is X discussed?” style source-navigation hybrids.

But keep the set bounded enough that “material completeness” is still judgeable.

## What failures you want these cases to trigger

Supported lookup should be designed mainly to catch these:

### `A1` — wrong abstention

The corpus clearly supports the answer, but the system says it cannot answer or says support is missing. The rubric explicitly lists this as a bad handling of `SUPPORTED`. 

### `P1` — provenance too weak

The answer is directionally right, but the source reference is too vague to inspect, such as only a document title with no page or section when more is recoverable. The rubric and support-semantics doc both treat inspectable provenance as part of the contract.

### `P2` — incorrect provenance

The cited location is wrong, even if the answer text happens to be right. The files are explicit that false provenance is a direct failure and that coarse real provenance is better than precise false provenance.

### `U1` — unsupported added detail

This is a common supported-lookup failure. The document says three requirements, and the model answers with five. Your rubric explicitly says unsupported detail is still a failure even if most of the answer is right. 

## Good supported lookup case shapes

These are good case shapes for MVP:

* “What retention period is specified for audit logs?”
* “Which team owns the migration checklist?”
* “What timeout value does the runbook recommend?”
* “In which section is tokenization discussed?”
* “What are the listed prerequisites for deployment?”

These all have:

* a bounded answer,
* clear local evidence,
* inspectable provenance,
* no dependence on unsupported capabilities.

## Bad supported lookup case shapes

I would avoid these in the supported-lookup bucket:

* questions requiring table reading or chart interpretation,
* broad comparisons,
* questions whose answer is spread across many documents,
* “why” questions that require substantial synthesis,
* questions where you are unsure whether the corpus fully supports the full answer shape.

Those belong in `partial_support`, `multi_source_synthesis`, `unsupported_scope`, or `ambiguous_conflict` instead.

## A simple build recipe

If I were building the supported-lookup slice first, I would do this:

1. Pick 8–12 corpus facts with crisp local support.
2. Split them across PDF and Markdown.
3. For each one, write a narrow question with one expected answer shape.
4. Annotate `support_state = SUPPORTED`.
5. Set minimum provenance before running the model.
6. Record one gold source location.
7. Make sure at least a few cases are paraphrased rather than exact text match.
8. Review each case and ask: “Would a human reviewer be able to say pass/fail on answer and provenance in under a minute?”

If not, the case is probably too broad.

## The operating rule

The cleanest test for supported lookup is:

**The model should answer directly and cite the right place, without abstaining and without adding anything the corpus does not say.** That is the essence of the rubric’s `SUPPORTED` behavior and provenance contract.
