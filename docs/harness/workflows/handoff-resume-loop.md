# Handoff / Resume Loop

## Purpose

The handoff / resume loop governs how work is paused, transferred, and safely resumed across agents, sessions, or context windows.

Its job is not to make substantive forward progress on the task or workstream itself. Its job is to:
- leave the current work in a resumable state,
- compress the current operational context without losing the control-plane truth,
- make the next executor able to continue without reconstructing the full history,
- reduce drift between what the work *is* and what the next agent *thinks* it is,
- preserve the current boundary conditions, risks, and next action.

This loop is the default operating loop whenever work is being intentionally paused or transferred.

## Outcome

A successful handoff / resume cycle produces one or more of the following:
- an updated task card or workstream card that accurately reflects the current state,
- a concise handoff note or resume summary,
- explicit statement of the current boundary condition,
- linked decisions, evidence, and open risks,
- a concrete `next_step` that another agent can execute,
- a clear indication of whether the item is ready to resume or must remain paused.

## When to use this loop

Use the handoff / resume loop when:
- an agent is stopping work before the slice is complete,
- work is being transferred to another agent,
- the current session is ending,
- the context window is becoming unreliable,
- a task or workstream is paused at a checkpoint, blocker, or approval boundary,
- work needs to be resumed after an interruption.

Do not use this loop for:
- initial task intake,
- ordinary active execution with no pause or transfer,
- checkpoint packaging itself,
- workstream coordination that is not actually pausing or transferring the work.

## Inputs

The handoff / resume loop expects:
- the current task card or workstream card,
- current Layer A, Layer B, Layer C, and Layer D state,
- current work log,
- any linked decisions, evidence, approvals, or review packets,
- the immediate reason for pausing or resuming.

The authoritative source remains the task or workstream card. The handoff note is a resumability aid, not a replacement source of truth.

## Core principles

### 1. The card stays authoritative

The handoff note should summarize the current state, but the task or workstream card must remain the authoritative operational record.

### 2. Preserve the control boundary exactly

If the item is blocked, at checkpoint, awaiting approval, validating, or complete, the handoff must preserve that fact precisely.

Do not hand off a paused item as if it were ready for normal execution.

### 3. Compress without hiding key decisions

A handoff should reduce replay cost, but it must not omit the decision, blocker, or scope boundary that explains the current condition.

### 4. Resume from the next step, not from the entire past

The goal of a good handoff is that the next agent can start from the current `next_step` with only limited supporting reread.

### 5. Distinguish transfer from reroute

A handoff transfers responsibility or context. It does not by itself change the slice, mode, or state unless the work itself has changed.

## Handoff procedure

### Step 1. Read the current authoritative artifact

Before handing off, read the current task card or workstream card in full.

Confirm:
- what the current slice or effort is,
- what Layer B mode is current,
- what Layer C control context or workstream wrapper applies,
- what Layer D state is current,
- what the current `next_step` is,
- what decisions, evidence, and risks are already linked.

If the card is stale, repair it before writing any handoff note.

### Step 2. Update the authoritative card first

Before writing a handoff note, update the task or workstream card so it matches reality.

Typical updates before handoff:
- refresh the summary if the slice changed shape,
- refresh Layer A if the problem shape materially changed,
- refresh Layer B if the dominant posture changed,
- refresh Layer C if a new boundary emerged,
- refresh Layer D to the actual current state,
- replace stale `next_step`,
- add current references, evidence refs, or decision refs,
- add a final work log entry for the current execution cycle.

Do not let the handoff note become newer or more correct than the card itself.

### Step 3. State why the handoff is happening

A handoff note should explicitly say why work is being paused or transferred.

Common reasons:
- session ending,
- context budget pressure,
- boundary reached,
- reviewer handoff,
- implementation handoff,
- work paused awaiting external input,
- workstream coordination passed to another agent.

This helps the next agent understand whether they should continue, wait, or switch posture.

### Step 4. Summarize the current slice or effort

Write a short summary of:
- what this task or workstream is about,
- what was accomplished in the current cycle,
- what the current boundary is,
- what still remains to be done.

Keep this summary short, but make it concrete.

A good summary should let the next agent answer:
- what is this item,
- what changed recently,
- what should happen next,
- what must not be forgotten.

### Step 5. Record the current control condition explicitly

The handoff must preserve the current Layer D reality in plain language.

Examples:
- `Task is active and ready to continue from the recorded next step.`
- `Task is blocked on missing fixture input; do not continue normal execution until the file is available.`
- `Task is at checkpoint; a review packet exists and implementation should not continue until the review outcome is recorded.`
- `Workstream is awaiting approval for stage 2 migration.`
- `Task is validating; the next agent should continue evidence generation rather than implementation.`

This protects against accidental continuation through a boundary.

### Step 6. Surface the most important linked artifacts

List the minimum set of linked artifacts the next agent should read.

Typical items:
- task or workstream card,
- decision record,
- review packet,
- approval packet,
- evidence bundle,
- code diff or PR,
- relevant RFC section,
- key log or benchmark output.

Do not require the next agent to reread everything. Point them to the smallest set of documents needed for correct resumption.

### Step 7. Make the next step concrete

The handoff should expose one concrete next action.

A good handoff next step is:
- specific,
- executable,
- consistent with the current state,
- aligned with the current Layer B posture.

Weak examples:
- `continue where I left off`
- `pick this up later`
- `finish the task`

Strong examples:
- `Write the failing regression test for nested list normalization using the reproduced input saved in the task refs.`
- `Review the linked RFC packet and decide whether the stage-1 intermediate schema is sufficient to lock.`
- `Wait for approval outcome; if approval is granted, create the child task for migration stage 2 rollout checks.`

### Step 8. Write the handoff note

Create or update the handoff note using the harness template if one exists.

At minimum, the handoff note should contain:
- item under handoff,
- handoff reason,
- current state and boundary,
- recent progress summary,
- important linked artifacts,
- open risks or traps,
- concrete next step,
- any specific instruction for the next executor.

The note should be concise enough to read quickly and complete enough to prevent drift.

### Step 9. Resume by reading authoritative state first

When resuming, the next agent should:
- read the current task or workstream card first,
- read the handoff note second,
- verify that the handoff is still current,
- check whether any linked decision, approval, or evidence has changed since the handoff,
- confirm that Layer D still permits the intended work.

Do not resume only from the handoff note.

### Step 10. Validate that the resume path is still correct

Before continuing work, confirm:
- the `next_step` is still valid,
- the current Layer B mode still matches the dominant posture,
- the current state has not changed due to external events,
- no new blocker, approval result, or review result has arrived,
- the work has not already been superseded or resliced.

If the handoff is stale, update the card and, if needed, write a new handoff note or reopen the relevant loop.

## Resume-specific guidance

### Resuming an `active` task

Read the current card, confirm no state drift, then continue from the recorded `next_step`.

### Resuming a `blocked` task

Do not continue normal execution until the blocker is actually cleared.

First verify the `unblock_condition`.

### Resuming a `checkpoint` item

Do not continue execution unless the review result is known and recorded.

If review is still pending, remain in the checkpoint/review loop.

### Resuming an `awaiting_approval` item

Do not continue across the gate until the approval result is recorded.

### Resuming a `validating` item

Resume in evaluation or verification posture, not in implementation posture, unless the routing has explicitly changed.

### Resuming a workstream

Read the workstream card first, then the relevant active child task cards, then the handoff note.

The next action may belong either to the workstream itself or to a specific child task.

## Handoff note quality bar

A handoff note is acceptable only if:
- it points to the authoritative artifact,
- it states why the handoff happened,
- it states the current control condition clearly,
- it summarizes the most recent meaningful progress,
- it names the minimum required linked artifacts,
- it gives a concrete next step,
- it helps the next agent resume without reconstructing the full history.

## Output quality bar

A handoff / resume cycle is acceptable only if:
- the authoritative card is up to date before handoff,
- the handoff note matches the authoritative card,
- the current Layer D boundary is preserved exactly,
- the next agent can tell whether to continue, wait, review, approve, validate, or stop,
- resume begins from the current state rather than stale assumptions.

## Anti-patterns

### Handoff note more accurate than the task card

Do not leave critical updates only in the handoff note.

### Hiding a blocker or checkpoint

Do not describe the work as ready to continue when the authoritative state is actually `blocked`, `checkpoint`, or `awaiting_approval`.

### Vague next steps

Do not hand off with instructions like `continue`, `finish up`, or `look into it`.

### Resume from summary only

Do not continue work by reading only the handoff note and skipping the current authoritative card.

### Missing trap or risk note

Do not omit the one or two risks most likely to cause the next agent to repeat failed work or cross the wrong boundary.

### Silent stale handoff

Do not trust an old handoff note blindly if decisions, approvals, or linked artifacts may have changed.

## Handoff / resume checklist

Use this checklist during handoff or resume.

- The authoritative task or workstream card was read.
- The card was updated before handoff if needed.
- The handoff reason is explicit.
- The current control condition is stated plainly.
- The smallest useful set of linked artifacts is listed.
- Open risks or traps are recorded.
- The next step is concrete and state-consistent.
- On resume, the authoritative card was read before relying on the handoff note.
- On resume, any changed decisions, approvals, or evidence were checked.
- The resume path still matches the current Layer D boundary.

## Minimal examples

### Example 1: end-of-session active handoff

Observed:
- a debugging task is still `active`,
- the cause has been narrowed to one normalization stage,
- the session is ending.

Good handoff result:
- task card updated with latest findings,
- handoff note records that the task remains `active`,
- linked reproduction input and code path are named,
- next step tells the next agent to write the failing regression test against the isolated stage.

### Example 2: checkpoint handoff to reviewer

Observed:
- an RFC task reached checkpoint,
- implementation must not continue until review outcome exists.

Good handoff result:
- task remains `checkpoint`,
- handoff note points to the review packet,
- note states that no implementation should proceed until review is recorded,
- next step is phrased for reviewer action rather than implementer action.

### Example 3: resume after approval outcome

Observed:
- workstream was previously `awaiting_approval`,
- approval has now been recorded.

Good resume result:
- next agent reads workstream card first,
- confirms approval ref is present,
- updates Layer D from `awaiting_approval` to `active`,
- creates or activates the next child task for the approved stage.

## Relationship to other loops

- Use the intake loop before handoff only when a task has not yet been normalized.
- Use the task execution loop to perform substantive task-level work between handoffs.
- Use the workstream loop to coordinate multi-slice work between handoffs.
- Use the checkpoint / review loop when the handoff occurs at a review boundary.
- Use the handoff / resume loop whenever work is intentionally paused, transferred, or resumed.

## Agent instruction shorthand

When operating as a handoff / resume agent:
1. read and update the authoritative card first,
2. state why the handoff or resume is happening,
3. preserve the exact current Layer D boundary,
4. summarize recent progress and the key linked artifacts,
5. expose the one concrete next step,
6. on resume, verify that the handoff is still current before continuing,
7. continue only if the current state permits it.
