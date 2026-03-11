An eval case is the **smallest unit of evaluation** in the harness. In your glossary, it is the atomic unit of execution, while a **scenario** is the reusable template that multiple cases can be derived from. So “source navigation” is a scenario class; “Where is tokenization discussed in Book A?” over a specific corpus is an eval case. 

The important distinction is that a case is not just “a question.” In your rubric, each evaluated item consists of:

* a corpus,
* a user question,
* a system response,
* returned source references,
* and optionally traces.
  And each item is annotated in **two layers**: question-level ground truth and run-level judgment.

So the anatomy of a good eval case is:

**1. Question-level definition**
This is what the corpus actually allows, independent of model behavior. The rubric says every question should have:

* one support state,
* one question class,
* and a minimum provenance expectation.

That means before you ever run the model, you decide things like:

* Is this question `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED_IN_CORPUS`, `UNSUPPORTED_QUESTION_TYPE`, or `AMBIGUOUS_OR_CONFLICTING`?
* What kind of question is it: `factual_lookup`, `source_navigation`, `multi_source_synthesis`, and so on?
* What provenance would count as inspectable here: document only, document + page, document + section, or document + page + section if available?

**2. Run-level judgment**
After the model answers, you score the run on:

* support alignment,
* scope control,
* provenance quality,
* abstention behavior,
* and overall trust outcome.

This is where the failure labels come in. A bad or borderline run then gets one primary failure label such as `U1`, `A2`, `P2`, `S1`, etc.

So the practical definition is:

> an eval case = one corpus-conditioned question with pre-annotated support expectations, plus a scored system run against that question.

That is why cases matter so much: they are the bridge between product promises and measurable behavior.

### What makes a case “good”

A good eval case is one where the reviewer can make stable judgments. In your rubric, disagreements should be resolved by first deciding support state, then whether the answer exceeded support, then provenance sufficiency, and only after that assigning failure labels. That means good cases are cases where support boundaries are legible. 

In practice, good cases usually have:

* a clear answer shape,
* a known support boundary,
* an explicit provenance expectation,
* and at least one plausible failure mode you care about.

That last point is my recommendation rather than a direct quote from the files: for your MVP, each case should mainly exist to expose one of the 8 first-class failures. That is the cleanest way to keep the eval set focused.

### Scenario vs case

This distinction is worth making explicit because it affects dataset design.

A **scenario** is a behavioral template. Examples from your rubric’s recommended first set are:

* direct lookup in PDF,
* direct lookup in Markdown,
* mixed PDF + Markdown synthesis,
* source navigation,
* partial support,
* unsupported in corpus,
* out-of-scope table/figure/image,
* conflicting-source,
* malformed or weakly structured documents. 

A **case** is one instantiated member of one of those scenario families:

* Corpus: `Book A.pdf`
* Question: “Where is tokenization discussed?”
* Support state: `SUPPORTED`
* Question class: `source_navigation`
* Minimum provenance: `document_page_and_section_if_available`
* Gold source: Book A, Chapter 4, pp. 112–118 

That is a case.

### What fields a case should contain

Your rubric already gives a compact JSONL schema. At minimum, question-level data should include:

* `query_id`
* `corpus_id`
* `question`
* `question_class`
* `support_state`
* `minimum_provenance`
* `gold_sources`
* optional notes. 

Then each run-level record adds:

* `run_id`
* `answer_text`
* `returned_sources`
* `support_alignment`
* `scope_control`
* `provenance_quality`
* `abstention_behavior`
* `overall_trust_outcome`
* primary failure label
* optional secondary causes
* severity / detectability / recoverability / confidence behavior. 

That schema is useful because it keeps **ground truth** separate from **observed behavior**.

### How eval cases relate to your 8 MVP failures

This is the part that matters for build prioritization.

A case should not just represent a topic; it should expose a trust risk. For your MVP, that means cases should be designed to trigger one of:
`U1, U2, A1, A2, P1, P2, I1, S1`. The rubric’s example families already line up with those risks. 

Examples:

* A **supported source-navigation** case is good for `A1`, `P1`, `P2`.
* A **partial-support synthesis** case is good for `U2`.
* An **unsupported-in-corpus** case is good for `A2` and `U1`.
* An **out-of-scope chart/table** case is good for `S1`.
* A **weakly structured Markdown or broken page-mapping** case is good for `I1`. 

So when you ask “what cases should we build?”, the best answer is not “more synthesis questions.” It is “more cases that are likely to reveal `U2`,” or “enough cases to tell whether `P2` is happening systematically.”

### A simple way to think about case design

For each case, decide four things upfront:

**What is the corpus reality?**
What is actually supported, partially supported, unsupported, conflicting, or out of scope?

**What would correct behavior look like?**
Direct answer, qualified answer, narrowed answer, surfaced conflict, or abstention. The rubric’s operating rule is: answer directly when support is clear, answer narrowly when support is partial, surface ambiguity when evidence conflicts, abstain when support is insufficient or out of scope.

**What provenance should be required?**
For PDFs, often page-level provenance. For Markdown, often section-path provenance. Provenance quality is part of the product contract, not an optional bonus.

**What is the target failure?**
Which top-level failure is this case mainly meant to catch? This last part is my recommendation, but it fits your rubric directly.

### Concrete examples

Here are a few clean MVP-style cases:

**Case A: supported navigation**

* Question: “Where is tokenization discussed?”
* Corpus reality: clearly supported in one book chapter
* Correct behavior: answer directly and cite the right pages/section
* Main failures exposed: `A1`, `P1`, `P2` 

**Case B: partial support**

* Question: “Summarize the chapter’s explanation of backpropagation and compare it to the appendix notes.”
* Corpus reality: appendix only partly supports the comparison
* Correct behavior: answer the supported parts, explicitly limit the comparison
* Main failure exposed: `U2` 

**Case C: unsupported in corpus**

* Question: “Which version of this library is currently recommended by the maintainer?”
* Corpus reality: not stated anywhere in the uploaded docs
* Correct behavior: say the corpus does not provide enough support
* Main failures exposed: `A2`, `U1` 

**Case D: unsupported question type**

* Question: “What values are shown in the benchmark chart?”
* Corpus reality: depends on chart/image interpretation outside MVP scope
* Correct behavior: state the limitation rather than invent values
* Main failure exposed: `S1` 

**Case E: ambiguous/conflicting**

* Question: “What retention period applies to audit logs?”
* Corpus reality: one doc says 90 days, another says 365
* Correct behavior: surface the conflict or qualify by source
* Main failure exposed: `A2`, sometimes `U2` 

### How many cases you need

Your rubric recommends an initial set of **50 to 100 annotated questions** and says it should intentionally include direct lookup, synthesis, navigation, partial support, unsupported-in-corpus, out-of-scope, conflicting-source, and malformed/weak-structure cases. 

For MVP build iteration, I would start smaller operationally: enough cases to cover each of the 8 first-class failures multiple times, across PDF, Markdown, and mixed corpora. That is an inference from the rubric rather than a quoted requirement, but it follows directly from the scoring and failure design.

### The most important mental model

Do not think of eval cases as “questions we ask the model.”

Think of them as **controlled trust probes**.

Each case should tell you something like:

* can the system answer when support is clear?
* can it stay narrow when support is partial?
* can it abstain when support is absent?
* can it cite inspectably?
* can it avoid false provenance?
* can it stay honest about scope limits?

That is what makes the case set valuable.

If useful, I can next turn this into a concrete MVP case template you can use to author cases consistently.
