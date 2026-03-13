Yes. I would keep these 8 exactly as the MVP first-class failures.

They already match the rubric’s trust contract: grounded answering, honest uncertainty, inspectable provenance, no fabricated provenance, and honest scope boundaries. The rubric also already says the Version 1 focus should be unsupported answers, bad abstention decisions, broken or weak provenance, visible ingestion/structure failures, and scope-boundary violations. 

The main adjustment I would make is this:

**do not redesign the failure list; redesign the case inventory and weighting around it.**

The current rubric already has the right evaluation primitives:

* question-level support state,
* minimum provenance expectation,
* run-level judgments for support alignment, scope control, provenance, and abstention,
* the same primary failure labels you selected. 



So for MVP I would keep these question states:

* `SUPPORTED`
* `PARTIALLY_SUPPORTED`
* `UNSUPPORTED_IN_CORPUS`
* `UNSUPPORTED_QUESTION_TYPE`
* `AMBIGUOUS_OR_CONFLICTING` 

Those are not extra complexity. They are the control surface that makes `U1/U2/A1/A2/S1` judgeable.

## What I would change

I would stop treating the scenario set as a broad coverage taxonomy and instead treat it as a **failure-exposure plan**.

That means every eval case should have:

* one **primary target failure**,
* optionally one secondary target failure,
* a support state,
* a provenance expectation,
* corpus-condition tags like `pdf`, `markdown`, `mixed`, `weak_structure`, `scanned_pdf`, `conflicting_sources`.

That is more useful than maintaining many scenario families that are not directly tied to the 8 launch failures.

## How I would remap the case surface

Keep the existing case families from the rubric, but rebalance them around the selected failures rather than equal conceptual coverage. The recommended first eval set already contains the right raw ingredients: supported lookup, source navigation, partial support, unsupported-in-corpus, out-of-scope, conflicting-source, and malformed/weak-structure cases. 

I would use them like this:

**1. Clearly supported lookup / localized answer cases**
Primary purpose: `A1`, `P1`, `P2`
Secondary exposure: `U1`
These are the cases where the model should simply answer and cite correctly. They are the best way to catch over-conservative behavior and weak provenance.

**2. Source-navigation cases**
Primary purpose: `P1`, `P2`, `A1`
These should stay first-class because provenance is part of the product promise, not just an accessory metric. The rubric already treats inspectable provenance as a core trust requirement. 

**3. Partial-support / incomplete-synthesis cases**
Primary purpose: `U2`
Secondary exposure: `A2`, `P1`
This is where you catch the most common RAG overreach: answering broadly when only a narrower answer is supported.

**4. Unsupported-in-corpus cases**
Primary purpose: `A2`
Secondary exposure: `U1`
These are the cleanest tests for honest abstention versus model-prior leakage.

**5. Unsupported-question-type cases**
Primary purpose: `S1`
Secondary exposure: `A2`
These are table/figure/image/OCR/external-world questions. The rubric explicitly says those are out of MVP scope and should be handled as limitations, not as grounded answers. 

**6. Ambiguous/conflicting cases**
Primary purpose: `A2`
Secondary exposure: `U2`
I would keep these, but smaller. They are not a separate MVP failure family, yet they are necessary because the rubric explicitly requires surfacing conflict rather than collapsing it into one confident answer. 

**7. Weak-structure / malformed-document cases**
Primary purpose: `I1`
Secondary exposure: `P1`, `P2`, sometimes `A1`
This should be treated as a corpus-condition slice, not just a question class. The same lookup or navigation question should be asked over both clean and structurally degraded inputs.

## What to reduce

I would de-emphasize:

* broad “localized explanation” cases that do not materially test provenance or support boundaries,
* generic multi-source synthesis unless it is specifically designed to trigger `U2` or `P2`,
* top-level KPI reporting for `R1`, `X1`, `G1`, `T1`, `N1`,
* `O1` in the semantic launch scorecard.

That is also consistent with the rubric, which already defines those as secondary cause labels for diagnosis rather than primary scoring. 

## Recommended MVP core pack

For the **build loop**, I would use a smaller core suite than the rubric’s broader 50–100 annotated target. The rubric’s larger number is fine for a fuller initial set, but for implementation iteration I would run a compact pack first. 

A good core pack would be about **28–36 cases**:

* 8 supported cases
  4 direct lookup, 4 source-navigation
* 6 partial-support cases
* 5 unsupported-in-corpus cases
* 5 unsupported-question-type cases
* 4 ambiguous/conflicting cases
* 4 weak-structure / ingestion-stress cases

That gives direct pressure on all 8 failures without spreading effort too thin.

If you want an even tighter first gate, use **24 cases**:

* 6 supported
* 4 partial-support
* 4 unsupported-in-corpus
* 4 unsupported-question-type
* 3 ambiguous/conflicting
* 3 ingestion-stress

## How I would prioritize the failures

Your priority order is basically right. I would make one small refinement:

**Tier 0 launch blockers**

* `U1`
* `A2`
* `P2`
* `S1`

These are direct trust breaks.

**Tier 1 strong product issues**

* `U2`
* `P1`

These often produce polished but unreliable answers.

**Tier 2 usefulness / operability**

* `A1`
* `I1`

These matter, but they are usually less dangerous than false support or false provenance.

That split is aligned with the rubric’s engineering guidance, which already calls out `U1`, `U2`, `A2`, `P2`, and `S1` as priority trust defects, with `A1` more about usefulness and `I1` more about ingestion/traceability quality. 

## One thing I would explicitly add to the schema

Add this to each question record:

```json
"primary_target_failure": "U2",
"secondary_target_failures": ["P1"],
"corpus_condition_tags": ["mixed", "partial_support", "page_groundable"]
```

That will make the eval set much easier to manage than relying on question class alone.

## Bottom line

Your 8-failure cut is the right MVP semantic surface.

I would:

* keep the 8 failures as first-class,
* keep support state explicit,
* keep secondary cause labels diagnostic only,
* rebalance the case inventory toward failure exposure,
* shrink the build-loop suite to a compact targeted pack,
* retain ambiguous/conflicting and source-navigation cases even though they are not standalone failure families, because they are how `A2`, `U2`, `P1`, and `P2` actually get tested. 

The most important adjustment is not “which labels exist.” It is: **each case should exist because it is meant to surface one of the 8 failures.**

I can turn this into a concrete case matrix next.
