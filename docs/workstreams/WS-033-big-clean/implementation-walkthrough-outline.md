# Implementation Walkthrough Outline — Supported Lookup First Slice

## 1. Purpose of this document

This document is a walkthrough outline for implementing the first executable vertical slice of the MVP.

It is not a full architecture specification.
It is a working guide for moving from:

- one design-driving user story,
- one Markdown corpus,
- supported lookup cases and answer keys,
- an existing system that may not fit the desired delivery flow,

to a first trustworthy implementation slice.

The first slice is intentionally narrow:

- **source type:** Markdown only
- **question family:** supported lookup
- **response mode:** direct answer with inspectable section-level provenance
- **main failures to pressure:** `A1`, `P1`, `P2`

---

## 2. How to use this document

For each section:

1. answer the design questions,
2. compare the desired shape to the current system,
3. decide whether to adapt, wrap, or defer existing components,
4. record one concrete implementation decision.

The goal is not to redesign everything.
The goal is to identify the minimum changes needed to produce one reliable supported-lookup loop.

---

## 3. Target first slice

### What this slice must do

The system should:

1. ingest one Markdown document,
2. preserve section structure,
3. answer supported lookup questions over that document,
4. return a short answer,
5. return inspectable provenance as **document + section path**,
6. avoid weak or false provenance.

### What this slice does not need yet

- PDF handling
- mixed-format behavior
- synthesis across sources
- advanced reranking
- broad abstention handling across all support states
- rich UI work

### Main questions

- What is the smallest end-to-end loop that proves the user story for supported lookup?
- What existing parts of the system already satisfy this loop?
- What parts of the current system actively work against this loop?
- What can be temporarily simplified or bypassed?

---

## 4. Existing-system alignment and gap map

This section is about the current system, not the target design.
Map the implementation you already have onto the desired delivery flow.

### Questions

- What are the current pipeline stages from upload to answer?
- Where does the current flow assume a different product shape than this MVP slice?
- Does the current system treat documents as flat chunks or preserve section hierarchy?
- Where is provenance created today?
- Is provenance carried through the pipeline or reconstructed late?
- What parts are tightly coupled and difficult to change?
- Which mismatches are superficial and which are structural?

### Output of this section

Produce a short gap map with three buckets:

- **keep as is**
- **adapt now**
- **defer / bypass for first slice**

---

## 5. Eval pack freeze

Before changing implementation, freeze the first evaluation pack.
This is the contract the slice must satisfy.

### Questions

- Which supported lookup cases are in the first pack?
- What is the exact gold short answer for each case?
- What is the expected support state for each case?
- What is the minimum provenance expectation for each case?
- Which cases are clean lookup cases and which are already borderline explanation or synthesis?
- Which cases are good for smoke testing and which are better for later regression?

### Output of this section

Define the first eval schema for each case:

- `case_id`
- `question`
- `gold_answer`
- `support_state`
- `minimum_provenance`
- `target_failures`
- `notes`

---

## 6. Corpus and document contract

Define the minimum object model for the source corpus and document identity.
Do not start with a large domain model.
Start with the fields required to preserve trust.

### Questions

- What is a corpus in this first slice: one file, one workspace, or one run input?
- What is the stable document identifier?
- What display name should appear in provenance?
- What source-type field exists, even if only `markdown` is used now?
- What metadata must survive every stage of the pipeline?
- What is allowed to remain implementation-local and not part of the stable contract yet?

### Output of this section

Define a minimal document contract such as:

- `corpus_id`
- `document_id`
- `display_name`
- `source_type`
- `content_version`
- `ingestion_timestamp`

---

## 7. Markdown structure recovery

This is the first major implementation decision.
For supported lookup over Markdown, section-aware structure is the most important foundation.

### Questions

- How will headings be parsed and normalized?
- What counts as a section path in the current implementation?
- How are nested headings represented?
- How are heading-less text blocks handled?
- How are lists, code blocks, and quotes preserved?
- Where can structure be lost in the current ingestion path?
- What is the fallback when the Markdown file is weakly structured?

### Output of this section

Define the section model:

- section id
- heading text
- heading level
- parent section
- section path
- raw text span / content block list

---

## 8. Retrieval unit design

Define the smallest retrieval unit that still preserves answerability and inspectable provenance.
For this slice, retrieval units should be section-aware, not arbitrary windows by default.

### Questions

- Is the retrieval unit a whole section, a subsection, or a bounded passage inside a section?
- When should a section be split into smaller units?
- What anchor metadata must every retrieval unit carry?
- How will retrieval units point back to the document and section path?
- Does the existing system already have a chunk model that can be adapted?
- Are there current chunking rules that destroy section semantics?

### Output of this section

Define a retrieval-unit contract such as:

- `unit_id`
- `document_id`
- `section_id`
- `section_path`
- `text`
- `token_count`
- optional local offsets

---

## 9. Retrieval behavior for supported lookup

For the first slice, retrieval only needs to support narrow questions over one Markdown corpus.
This section should stay operational, not theoretical.

### Questions

- What retrieval method will be used first?
- How many units are retrieved for a supported lookup question?
- How is retrieval quality inspected during debugging?
- Is there a cheap way to include section-title text in retrieval scoring?
- How often does the current system retrieve adjacent but not actually supporting units?
- Is a reranker necessary in the first slice, or is it premature?

### Output of this section

Define the first retrieval policy:

- candidate generation method
- number of units returned
- any section-title boosting or adjacency rules
- trace format for retrieved results

---

## 10. Support and answerability gate

Even in a supported-lookup slice, the system should not emit final answers without an explicit answerability check.
This does not need to be a complex classifier yet.

### Questions

- Where in the current flow can answerability be checked before answer emission?
- What simple heuristic or prompt-level rule will decide whether evidence supports a direct answer?
- What counts as sufficient support for a lookup question?
- What should happen if retrieval finds related text but not answer-supporting text?
- How will the system fail closed when provenance is too weak?

### Output of this section

Define a minimal gate with explicit outputs such as:

- `answer_directly`
- `answer_narrowly`
- `abstain`
- `insufficient_provenance`

For the first slice, only `answer_directly` and `abstain/insufficient_provenance` may be implemented.

---

## 11. Answer composition contract

The answer should be treated as a structured payload, not just model text.

### Questions

- What is the maximum answer shape for supported lookup: one sentence, short paragraph, bullet list?
- How will the answer remain bounded to the retrieved evidence?
- How should the answer quote or paraphrase source text?
- What parts of the answer are generated and what parts are assembled deterministically?
- How will unsupported detail be suppressed?
- Can the current system separate answer text generation from provenance assembly?

### Output of this section

Define a result payload such as:

- `answer_text`
- `support_state_prediction`
- `citations[]`
- `confidence_or_policy_note` (optional)

---

## 12. Provenance and citation payload

This section is central to the slice.
The goal is not perfect citation precision. The goal is inspectable, correct provenance.

### Questions

- What is the minimum provenance for Markdown in this slice?
- How is section path rendered to the user?
- What does the system do when multiple units from the same section support the answer?
- What does the system do when the answer is supported but section path reconstruction is weak?
- Can provenance be verified from stored metadata, or is it inferred late?
- Where could false provenance be introduced today?

### Output of this section

Define the citation payload such as:

- `document_id`
- `display_name`
- `section_path`
- `unit_id` (internal)
- optional snippet / highlighted support text

---

## 13. Logging and traces

Without traces, you will not be able to understand whether failures come from ingestion, retrieval, answering, or provenance assembly.

### Questions

- What run-level information is logged today?
- What is missing to diagnose `A1`, `P1`, and `P2`?
- Can each answer be traced back to retrieved units?
- Are prompts, retrieved texts, and returned citations inspectable after a run?
- What can be logged cheaply now without building a full observability layer?

### Output of this section

Define a minimal trace record containing:

- query text
- selected document ids
- retrieved units and scores
- final answer text
- final citation payload
- decision outcome from the answerability gate

---

## 14. Eval harness and reviewer loop

Implementation should be driven by repeatable case runs, not only manual spot checks.

### Questions

- How will cases be executed against the current system?
- What result record will be stored for each run?
- How will gold answer comparison be done for supported lookup?
- How will provenance quality be reviewed?
- What is the first judgment loop: manual review, scripted checks, or both?
- Which checks can be automated immediately and which require human review?

### Output of this section

Define the first evaluation record:

- case input
- system output
- answer correctness judgment
- provenance usability judgment
- provenance correctness judgment
- notes on failure label if applicable

---

## 15. First-pass failure policy

Do not attempt to score the entire failure taxonomy in the first loop.
Use only the failures pressured by this slice.

### Questions

- What does `A1` look like in the current system?
- What does `P1` look like in the current system?
- What does `P2` look like in the current system?
- Which of these can be partially detected automatically?
- Which failure should block acceptance of a run even if the answer text looks good?

### Output of this section

Define first-pass review rules:

- fail on wrong abstention for clearly supported lookup
- fail on weak provenance when section path is recoverable
- fail on incorrect provenance even if answer text is correct

---

## 16. Iteration plan

After the first slice runs end to end, improvement should be staged.

### Questions

- What is the first likely bottleneck: structure recovery, retrieval, answer control, or citation assembly?
- What changes are safe to try without destabilizing the whole flow?
- What should be tuned first if supported answers are correct but provenance is weak?
- What should be tuned first if retrieval is missing obvious sections?
- What evidence is sufficient to move to the next slice?

### Output of this section

Define a short iteration order, for example:

1. fix structure and section recovery,
2. fix provenance propagation,
3. improve retrieval coverage,
4. tighten answer boundedness,
5. add more cases.

---

## 17. Expansion gates after the first slice

Do not expand by default.
Expand only when the first slice is stable enough to trust.

### Questions

- What conditions must be true before adding a second Markdown document?
- What conditions must be true before adding source navigation as a formal slice?
- What conditions must be true before adding partial-support cases?
- What conditions must be true before introducing PDFs?
- What signs would show that the current architecture cannot be adapted and needs a more structural redesign?

### Output of this section

Define explicit expansion gates for:

- multi-document Markdown
- source navigation
- partial support
- mixed-format corpus
- PDF ingestion

---

## 18. Immediate next action checklist

Use this as the implementation starting point.

1. Freeze the supported lookup eval pack.
2. Write the minimal document and retrieval-unit contracts.
3. Inspect the current ingestion flow for structure loss.
4. Implement or adapt heading-aware Markdown segmentation.
5. Ensure retrieval units preserve section path.
6. Add a minimal answerability/provenance gate.
7. Return structured answer + citation payload.
8. Log retrieved units, answer, and citations.
9. Run the first supported lookup pack.
10. Review failures only through `A1`, `P1`, and `P2`.

---

## 19. Open implementation notes

Use this section during implementation to capture decisions that do not yet deserve a stable design document.

Suggested prompts:

- What existing assumption in the current system caused the most friction?
- Which shortcut was acceptable for the first slice?
- Which shortcut must not survive into the next slice?
- What should become a stable contract after the first successful loop?
