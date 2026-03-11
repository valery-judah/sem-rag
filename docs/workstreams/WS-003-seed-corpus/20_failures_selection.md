For this MVP, I would make **8 failures** first-class and treat them as the core eval surface. That selection follows your own trust contract: grounded answering, honest uncertainty, inspectable provenance, no fabricated provenance, and explicit handling of out-of-scope questions. Your rubric also explicitly says the failures that matter most for Version 1 are unsupported answers, bad abstention decisions, broken or weak provenance, visible ingestion/structure failures, and scope-boundary violations.   

I would **not** make secondary cause labels like `R1`, `G1`, `T1`, `N1` top-level KPI failures for the MVP. Those are useful for diagnosis, but they are not the product-facing trust failures the user experiences. I would also keep `O1` operational failure in your logging and dashboards, but not in the primary semantic eval pack unless reliability is one of the immediate launch gates. 

## Recommended critical 8

### 1) U1 — Unsupported answer

**Why it is critical:** this is the clearest trust break. The system says something the corpus does not support. That directly violates grounded answering.
**What to test:** factual lookup, explanation, and synthesis questions where the model is tempted to fill gaps from priors.
**Pass condition:** every material claim is attributable to corpus evidence.
**Typical failure signature:** invented detail, external knowledge blended in, or overstating what a book/note says.
**Priority:** highest.  

### 2) U2 — Partially supported answer presented as complete

**Why it is critical:** this is the most common “looks good but is wrong” RAG failure in MVP systems. It is especially dangerous for mixed-source synthesis because the answer can appear polished while quietly exceeding support.
**What to test:** partial-support questions and multi-source questions with incomplete evidence.
**Pass condition:** answer is explicitly narrowed or qualified.
**Typical failure signature:** broad synthesis anyway, full comparison from incomplete evidence, omitted uncertainty.
**Priority:** highest.  

### 3) A1 — Wrong abstention

**Why it is critical:** this is a usefulness failure. If supported questions still get “not enough evidence,” the product feels weak even when the corpus contains the answer.
**What to test:** clearly supported lookup and source-navigation questions in both PDF and Markdown.
**Pass condition:** direct answer when support is materially sufficient.
**Typical failure signature:** unnecessary refusal, over-narrowing, or saying support is missing when it exists.
**Priority:** high, but below U1/U2/A2/P2.  

### 4) A2 — Failed abstention

**Why it is critical:** this is the inverse of A1 and is more dangerous. The rubric already treats it as a high-severity trust issue.
**What to test:** unsupported-in-corpus, unsupported question type, and conflicting-evidence questions.
**Pass condition:** abstain, qualify, or surface ambiguity when support is weak, absent, or conflicting.
**Typical failure signature:** strong answer to unsupported questions, confident collapse of conflicting sources into one claim.
**Priority:** highest.  

### 5) P1 — Provenance missing or too weak to inspect

**Why it is critical:** your product promise is not just “answer,” but “answer plus inspectable evidence.” Weak provenance undermines trust even when the answer text is directionally right.
**What to test:** whether answers return usable document + page/section references appropriate to PDF vs Markdown.
**Pass condition:** user can navigate back to support with realistic granularity.
**Typical failure signature:** document name only, no page when page should exist, vague nearby evidence.
**Priority:** high.  

### 6) P2 — Incorrect provenance

**Why it is critical:** this is worse than weak provenance. False provenance is a direct trust-contract violation because the system appears inspectable while lying about support.
**What to test:** page/section/document accuracy, especially after chunking and answer assembly.
**Pass condition:** cited location actually supports the claim.
**Typical failure signature:** wrong page, wrong section, wrong document, fabricated anchor.
**Priority:** highest.  

### 7) I1 — Ingestion or structure failure visible in answer quality

**Why it is critical:** your MVP depends on lightweight structure recovery and coarse traceability. If ingestion corrupts headers, page mapping, or section boundaries, retrieval and provenance both degrade.
**What to test:** malformed PDFs, weakly structured Markdown, code blocks, heading loss, broken page mapping.
**Pass condition:** structure remains usable enough for retrieval and citation in common cases.
**Typical failure signature:** lost headings, page mismatch, collapsed Markdown sections, formatting damage changing meaning.
**Priority:** high for mixed-format MVP, because PDF/Markdown normalization is itself a feasibility hypothesis.  

### 8) S1 — Scope-boundary failure

**Why it is critical:** your MVP is explicitly not promising OCR, table/figure understanding, or external-world answers. If the system answers these as though grounded, it breaks scope honesty.
**What to test:** table-dependent, figure-dependent, image-dependent, scanned PDF, and external-knowledge questions.
**Pass condition:** explicit limitation or abstention.
**Typical failure signature:** invented chart values, acting as if OCR-poor PDFs were parsed correctly, answering outside-corpus world facts.
**Priority:** highest among out-of-scope behaviors.  

## Why these 8 are the right MVP set

These 8 cover the full trust loop:

* **Can it stay inside evidence?** `U1`, `U2`
* **Can it decide when to answer vs abstain?** `A1`, `A2`
* **Can the user inspect support?** `P1`, `P2`
* **Can the ingestion layer preserve enough structure for QA to work?** `I1`
* **Can it stay honest about MVP limits?** `S1`

That maps cleanly to your product definition and success criteria: answer from the uploaded corpus, keep answers tied to source references, let users inspect evidence, and fail transparently rather than fabricate.  

## What I would de-prioritize

I would **de-prioritize `O1` as a semantic eval label** for now. Track it in reliability dashboards, but don’t let it crowd out answer-trust failures in the MVP eval pack. Runtime failures matter operationally; they do not tell you whether the core product contract is working.
I would also keep `R1`, `X1`, `G1`, `T1`, `N1` as **secondary diagnosis labels only**. They are useful after a failure is found, not as the primary thing you optimize the eval around. 

## Minimal schema I would use for these 8

For each failure, define:

* `failure_code`
* `user_visible_risk`
* `trigger_rule`
* `severity_default`
* `detectability`
* `recoverability`
* `canonical_test_questions`
* `expected_correct_behavior`
* `bad_example_patterns`

That is enough to make the taxonomy usable by both human reviewers and automated evaluation later. Your rubric already has most of this structure; the main change is reducing the top-line pack to the 8 failures above and keeping the rest diagnostic. 

## Recommended order of evaluation work

1. `U1`, `A2`, `P2`
2. `U2`, `P1`
3. `A1`, `S1`
4. `I1`

That order matches your own engineering guidance, where high `U1`, `U2`, `A2`, `P2`, and `S1` are priority trust defects. 

If you want, I can turn this into a compact **JSON/YAML failure spec** you can drop directly into your eval repo.
