# Checkpoint / Review Loop

## Purpose

The checkpoint / review loop governs what happens when task-level or workstream-level progress intentionally pauses at a review boundary.

Its job is not to continue normal execution past that boundary. Its job is to:
- make the review boundary explicit,
- package the current state of the work into a reviewable form,
- expose the decision, interpretation, or approval request clearly,
- preserve enough context that another human or agent can evaluate the boundary without replaying the whole work history,
- record the resulting review outcome in a way that can safely restart, redirect, or terminate the work.

This loop is the default operating loop whenever Layer D is `checkpoint` or when a review-oriented Layer C overlay is active and a boundary has been reached.

## Outcome

A successful checkpoint / review cycle produces one or more of the following:
- a well-formed review packet or decision request,
- a clear statement of what is being asked from the reviewer,
- linked evidence and relevant references,
- a recorded review outcome,
- an updated Layer D state such as `checkpoint -> active`, `checkpoint -> awaiting_approval`, `checkpoint -> blocked`, `checkpoint -> complete`, or `checkpoint -> cancelled`,
- updated `next_step`, `decision_ref`, `approval_ref`, `checkpoint_reason`, or `evidence_refs` as appropriate.

## When to use this loop

Use the checkpoint / review loop when:
- a task or workstream has reached a declared review boundary,
- Layer D is `checkpoint`,
- Layer C includes `review_gatekeeper` and the pause condition has been met,
- the next move requires human interpretation, direction selection, or review of findings,
- the work should stop until a packet is reviewed or a decision is made.

Do not use this loop for:
- ordinary active execution,
- raw intake normalization,
- workstream coordination that has not yet reached a real review pause,
- hard approval handling after a checkpoint has already become an approval gate, except insofar as the checkpoint produces that approval request.

## Inputs

The checkpoint / review loop expects:
- a task card or workstream card that has reached a review boundary,
- a clear `checkpoint_reason` or equivalent narrative explanation,
- the current Layer A, Layer B, Layer C, and Layer D context,
- relevant work log history,
- evidence, findings, or artifacts produced so far,
- any policy or template guidance relevant to the review packet.

The authoritative source remains the task or workstream card, but the review packet is the primary artifact surfaced to the reviewer.

## Core principles

### 1. A checkpoint is a deliberate pause, not a soft suggestion

Once a review boundary is reached, the loop should not continue autonomous forward execution past that point.

### 2. The review packet should minimize replay cost

A reviewer should not need to reconstruct the entire task from chat history, memory, or raw logs.

### 3. Ask for one clear thing

The packet should make explicit what decision, interpretation, or direction is being requested.

### 4. Preserve options and rationale, not just conclusions

A good checkpoint packet records what was considered, what was observed, and why the current recommendation exists.

### 5. Record the result in control-plane terms

The review outcome should be reflected through Layer D, related refs, and the next step. It should not remain trapped inside unlinked prose.

## Checkpoint / review procedure

### Step 1. Confirm that a real checkpoint boundary exists

Before entering this loop, verify that the pause is legitimate.

A real checkpoint usually exists when:
- further progress depends on human interpretation,
- multiple viable options now require selection,
- the work has produced findings that should be reviewed before continuation,
- an RFC, plan, contract, or evaluation result is ready for review,
- a workstream milestone explicitly requires review before the next stage.

Do not use `checkpoint` as a vague synonym for “temporarily stopped.”

If the work is simply blocked, use `blocked` instead.
If the work has crossed into a hard approval gate, it may move to `awaiting_approval` after or instead of the checkpoint.

### Step 2. Read the authoritative task or workstream card

Read the current task card or workstream card in full.

Confirm:
- what slice or scope is under review,
- why the checkpoint was reached,
- what Layer B mode produced the current findings,
- whether Layer C includes `review_gatekeeper`,
- what state the item is in now,
- what evidence, decisions, or risks are already linked.

If the card is stale or unclear, update it before preparing the review packet.

### Step 3. Define the review question explicitly

Write the review request as a concrete question.

Good examples:
- `Which of the three migration paths should the workstream take next?`
- `Is the proposed intermediate schema sufficient to lock as the contract for stage 1?`
- `Do the evaluation findings justify proceeding to implementation, or is additional analysis required?`
- `Should this refactor stop here and be split into two safer slices?`

Weak examples:
- `Please review`
- `Thoughts?`
- `Need feedback`

The packet should make it obvious what outcome is being requested.

### Step 4. Prepare the review packet

Create or update a review artifact using the relevant template if one exists.

At minimum, the review packet should contain:
- scope under review,
- current objective,
- current Layer B mode or most relevant recent mode,
- why the checkpoint was reached,
- relevant findings or progress summary,
- options considered,
- recommendation if one exists,
- risks or tradeoffs,
- linked evidence or references,
- explicit review question,
- requested outcome.

The packet should be concise but decision-useful.

### Step 5. Link evidence and supporting artifacts

Attach or reference the artifacts needed to evaluate the checkpoint.

Typical supporting artifacts:
- RFC sections,
- draft contracts,
- architecture sketches,
- evaluation summaries,
- test outputs,
- diff summaries,
- migration readiness notes,
- benchmark results,
- linked child task findings for workstream-level review.

Do not dump raw material without a summary. Review packets should point to evidence, not force reviewers to sift blindly.

### Step 6. Verify Layer D and companion fields before pausing

Before the review is handed off, ensure Layer D matches reality.

Usually this means:
- `state: checkpoint`
- `checkpoint_reason` filled
- `next_step` updated to reflect the expected review outcome or handoff
- `decision_ref` empty if no decision has yet been recorded
- `approval_ref` empty unless the checkpoint already packages an approval request
- `evidence_refs` populated where relevant

If the item should actually be `awaiting_approval`, record that explicitly rather than leaving it in a vague checkpoint state.

### Step 7. Hand off the packet for review

The packet should be ready to hand to:
- a human reviewer,
- a supervising agent,
- a reviewer-role prompt,
- or a later session acting in reviewer mode.

The handoff should make clear:
- what needs to be reviewed,
- what decision is needed,
- what happens after each likely outcome.

If the harness uses separate review templates or prompts, link them here.

### Step 8. Record the review outcome

When review results arrive, record them in the authoritative task or workstream card and in any linked decision record.

Typical review outcomes:
- proceed as proposed,
- proceed with modifications,
- gather more evidence,
- split or reslice the work,
- escalate to approval,
- pause due to unresolved issues,
- terminate the slice or workstream.

The result should not remain only in freeform commentary.

### Step 9. Transition Layer D based on the outcome

After review, update Layer D to match the new control condition.

Common transitions:
- `checkpoint -> active` when direction is confirmed and execution may resume,
- `checkpoint -> awaiting_approval` when review produced a hard approval request,
- `checkpoint -> blocked` when review identified a blocking unresolved issue,
- `checkpoint -> validating` when the next required step is evidence generation,
- `checkpoint -> complete` when the checkpoint itself satisfied the closure condition,
- `checkpoint -> cancelled` when the work should not continue.

Do not leave the item in `checkpoint` after the review result is known unless another review pause is immediately the correct current condition.

### Step 10. Refresh next step and routing after review

A review result often changes not only the state but also the route.

Reassess:
- `next_step`,
- current Layer B mode,
- need for reslicing,
- need for workstream promotion or retirement,
- whether `governance_escalation` or `awaiting_approval` now applies.

Examples:
- an RFC review may move a task from `contract_builder` to `routine_implementer`,
- an architecture review may force a split into multiple child tasks,
- evaluation review may keep the task in `quality_evaluator` and request more evidence,
- migration review may escalate the workstream into an approval gate.

## Review packet quality bar

A review packet is acceptable only if:
- the scope under review is explicit,
- the reason for the checkpoint is explicit,
- the review question is explicit,
- the main findings or options are summarized,
- the recommendation and tradeoffs are understandable,
- evidence and references are linked,
- the reviewer can decide without reconstructing the entire work history.

## State-specific guidance

### When a task is at checkpoint

The packet should focus on the current slice.

Include only enough surrounding context to explain why this slice reached review.

### When a workstream is at checkpoint

The packet should focus on the milestone or cross-slice decision.

Summarize only the child-task findings needed to understand the workstream-wide question.

### When checkpoint turns into approval

If the review result is that a hard signoff is now required, transition the item to `awaiting_approval` and prepare or link the approval packet.

Do not keep approval work hidden inside checkpoint prose.

### When review requests more evidence

Transition to the state that matches the next true condition.

Often this means:
- `active` if the next step is straightforward follow-up work,
- or `validating` if evidence generation is now the dominant activity.

## Output quality bar

A checkpoint / review cycle is acceptable only if:
- the review boundary is real and explicit,
- the task or workstream card matches the current paused state,
- the review packet clearly asks for a specific outcome,
- evidence and findings are linked at the right level of summary,
- the review outcome is recorded in the authoritative artifact,
- Layer D is updated to reflect the post-review reality,
- a concrete next step or terminal condition exists after review.

## Anti-patterns

### Checkpoint without a real question

Do not pause work for “review” if no real interpretation, option selection, or boundary decision exists.

### Dumping raw material instead of packaging it

Do not hand reviewers a pile of notes, logs, and diffs with no summary or question.

### Continuing execution through a checkpoint

Do not keep implementing, migrating, or evaluating past a declared review boundary as if the checkpoint were advisory.

### Leaving the outcome only in prose

Do not let the review result live only in comments, chat, or packet text. Reflect it in Layer D, refs, and next steps.

### Stale checkpoint state

Do not leave a task or workstream in `checkpoint` after the review has already concluded.

## Checkpoint / review checklist

Use this checklist during or at the end of the loop.

- A real checkpoint boundary exists.
- The authoritative card was read and, if needed, repaired.
- The review question is explicit.
- A review packet or equivalent summary artifact exists.
- Findings, options, recommendation, and tradeoffs are summarized.
- Evidence and references are linked.
- Layer D and companion fields reflect the paused state before review.
- The review outcome was recorded when available.
- Layer D was transitioned after review.
- A concrete next step or terminal state is explicit.

## Minimal examples

### Example 1: RFC review checkpoint

Observed:
- an RFC section is sufficiently drafted,
- implementation should not begin until the contract is reviewed.

Good checkpoint result:
- task transitions to `checkpoint`,
- a review packet summarizes the proposed contract, alternatives, and open question,
- the review asks whether the contract is sufficient to proceed,
- after approval of direction, the task moves back to `active` and may reroute to `routine_implementer`.

### Example 2: workstream architecture checkpoint

Observed:
- several child tasks produced findings,
- the workstream needs a decision on which architecture path to pursue.

Good checkpoint result:
- workstream-level review packet created,
- child-task findings summarized at the workstream level,
- `review_gatekeeper` remains active,
- workstream Layer D is `checkpoint`,
- after review, the workstream creates or activates the next child slice aligned with the selected path.

### Example 3: review demands more evidence

Observed:
- evaluation packet is reviewed,
- reviewer decides the findings are inconclusive.

Good checkpoint result:
- review outcome is recorded,
- task leaves `checkpoint`,
- task transitions to `validating` or `active` depending on the nature of the follow-up work,
- next step is updated to gather the additional required evidence.

## Relationship to other loops

- Use the intake loop to shape new work before any checkpoint exists.
- Use the task execution loop to produce the work that eventually reaches a checkpoint.
- Use the workstream loop to coordinate checkpoints at effort scope.
- Use the checkpoint / review loop to package and resolve review boundaries.
- Use the handoff/resume loop when the paused item is being transferred across agents or sessions.

## Agent instruction shorthand

When operating as a checkpoint / review agent:
1. verify that a real review boundary exists,
2. read the authoritative task or workstream card,
3. define the exact review question,
4. prepare a concise review packet with findings, options, recommendation, and evidence,
5. set or confirm Layer D as `checkpoint` until the outcome is known,
6. record the review result in the authoritative artifact,
7. transition Layer D to the correct post-review state,
8. leave a concrete next step or terminal decision.
