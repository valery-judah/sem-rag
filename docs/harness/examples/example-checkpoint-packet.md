

# Example Checkpoint Packet

This example shows what a review-ready checkpoint packet can look like when a task reaches a real review boundary.

It is intentionally concise and decision-oriented. The goal is to show:
- how the packet frames one explicit review question,
- how it summarizes the relevant findings without replaying the whole work history,
- how options, recommendation, and tradeoffs are made visible,
- how the packet supports a real checkpoint transition rather than acting as a vague status note.

```md
# Review Packet

## Item Under Review

- item_type: task
- item_id: T-2026-03-06-002
- title: Define intermediate schema acceptance contract
- current_mode: contract_builder
- current_state: checkpoint

## Review Question

Is the proposed phase-1 intermediate schema sufficiently defined to lock as the contract for downstream implementation and evaluation work?

## Why This Checkpoint Exists

The task has completed the current contract-definition slice. Further progress should not continue into implementation-oriented child tasks until the schema boundary is reviewed and either accepted, modified, or sent back for more clarification.

## Current Objective

Define the minimum viable intermediate schema that phase-1 segmentation work can rely on as a stable contract between upstream parsing output and downstream segmentation logic.

## Scope Under Review

In scope for this checkpoint:
- required top-level schema fields
- expected block representation boundaries
- invariants needed for phase-1 segmentation
- explicit exclusions for later phases

Out of scope for this checkpoint:
- full production schema evolution
- retrieval optimization implications beyond phase 1
- downstream UI or presentation concerns
- broader graph-structured document modeling

## Findings Summary

The current draft proposes a bounded intermediate schema intended for phase 1 only. The contract is designed to support segmentation without prematurely committing to richer graph-level structures.

Current draft characteristics:
- block-oriented output structure
- explicit required fields for block identity, type, content span, and parent/child relationships needed for phase 1
- explicit statement that advanced metadata and graph enrichments are deferred
- acceptance criteria focused on structural consistency and segmentability rather than full semantic completeness

The draft appears sufficient for early implementation slices if phase-1 scope remains constrained. The main remaining question is whether the parent/child and block-boundary semantics are explicit enough to prevent later reinterpretation during implementation.

## Options Considered

### Option 1 — Accept the schema as drafted

Pros:
- unblocks implementation and evaluation slices immediately
- preserves narrow phase-1 scope
- avoids premature schema expansion

Cons:
- some ambiguity may remain around edge cases in nested or irregular block structures

### Option 2 — Accept with targeted clarifications

Pros:
- preserves progress while reducing ambiguity
- keeps schema small but makes boundary semantics more explicit
- likely reduces later rerouting into contract clarification

Cons:
- adds a short additional pass before downstream child tasks proceed

### Option 3 — Reject for now and request more contract work

Pros:
- reduces risk of implementation on an unstable contract
- gives more time to settle edge cases

Cons:
- delays downstream slices
- risks over-expanding the contract before phase-1 implementation begins

## Recommendation

Recommend **Option 2 — Accept with targeted clarifications**.

The current schema is close to sufficient, but adding one more explicit clarification pass around nested block boundary semantics and parent/child invariants would materially reduce later ambiguity without bloating the contract.

## Tradeoffs / Risks

- Accepting too early may push contract ambiguity downstream into implementation tasks.
- Over-clarifying now may cause premature expansion of phase-1 scope.
- Rejecting the draft entirely may delay useful downstream work without proportional benefit.
- The main operational risk is not missing fields; it is inconsistent interpretation of structural invariants across later slices.

## Linked Evidence / References

- authoritative task card: `docs/harness/active/tasks/T-2026-03-06-002-intermediate-schema-contract.md`
- parent workstream: `docs/harness/active/workstreams/W-2026-03-segmentation.md`
- related RFC draft: `docs/rfc/hierarchical-segmentation.md`
- routing policy: `docs/harness/policies/routing-rules.md`

## Requested Outcome

Choose one of the following:
- accept as drafted and return the task to `active` for downstream implementation-aligned slicing,
- accept with targeted clarifications and return the task to `active` with a concrete clarification next step,
- request more evidence or clarification and move the task to `validating` or back to `active` under contract work,
- escalate to approval if this boundary requires signoff before downstream slices proceed.

## Suggested Post-Review Next Step

If Option 2 is accepted:
- update the contract task with explicit clarifications for nested block boundary semantics,
- return the task to `active`,
- then create or activate the downstream child task for segmentation logic design under the reviewed contract.
```

## Why this example is shaped this way

A few things are deliberate here:

- The packet asks one clear review question.
- It is anchored to the authoritative task and current checkpoint state.
- It summarizes the work at decision level rather than dumping raw draft text.
- The options are real operational choices, not decorative alternatives.
- The recommendation is explicit but does not hide the tradeoffs.
- The requested outcome section makes the post-review transition legible.

## What to notice

This example is a good reference when:
- a task has reached `checkpoint`,
- a contract, RFC section, or design boundary needs review,
- the reviewer should be able to decide without replaying the whole task history,
- the packet should clearly support a post-review Layer D transition.

## Possible variations

A checkpoint packet like this would look different if:
- the item under review were a workstream milestone rather than a single task,
- the dominant work were evaluation findings rather than contract definition,
- the likely outcome were escalation to approval instead of direct continuation,
- the main question were option selection across architecture paths rather than acceptance of a near-final draft.