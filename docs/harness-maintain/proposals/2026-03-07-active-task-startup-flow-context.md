# Active-task startup flow context

## Context

This note records a concrete harness gap observed while starting a fresh coding-agent instance and trying to pick an existing task to implement.

The harness already has a mechanism for seeing active work through `docs/harness/indexes/active-tasks.md`, but the startup flow is not currently explicit enough to make task discovery and task selection reliable for a new agent.

The immediate concrete mismatch is that `docs/harness/indexes/active-tasks.md` lists multiple live tasks, while `docs/harness/active/tasks/` currently contains only one authoritative task card.

That breaks confidence in the startup path. A new agent cannot tell whether the queue is trustworthy, illustrative, stale, or only partially maintained, and therefore cannot safely treat it as the first step for selecting work.

This note is not an implementation patch. It is context for follow-up harness changes that should make startup behavior explicit and reliable.

## Current friction

### 1. The harness has visibility artifacts but not a clean startup search-select flow

The harness explains authority order well and it explains execution, intake, and resume loops well. What it does not currently spell out is the entry flow for a new coding agent that needs to discover current work before it knows which task card to open.

Several docs assume the target task is already known:

- `docs/harness/AGENTS.md`
- `docs/harness/workflows/task-execution-loop.md`
- `docs/harness/workflows/handoff-resume-loop.md`
- `docs/harness/prompts/execution-agent.md`
- `docs/harness/prompts/resume-agent.md`

That assumption is acceptable once a task has already been selected. It is not enough for the first startup step of a new agent instance.

### 2. The current active-task queue is not trustworthy enough as a startup surface

`docs/harness/indexes/active-tasks.md` presents itself as a live derivative queue, but its entries do not currently correspond to the actual authoritative task-card set in `docs/harness/active/tasks/`.

Once that mismatch exists, the queue no longer functions as a safe discovery surface for implementation work.

### 3. The current queue mixes executable and non-executable states

The active-task index currently mixes items in states such as:

- `active`
- `draft`
- `checkpoint`

That makes the queue less useful for the narrower question a fresh coding agent usually has at startup:

"Which task can I execute now?"

The harness needs a cleaner default answer to that question.

## Desired startup flow

The intended startup flow for a fresh coding agent should be:

1. Start from the active-task queue.
2. Use that queue as the discovery surface for executable work.
3. Select one queue entry.
4. Open the linked authoritative task card before any execution or resume action.
5. Continue through the correct workflow loop based on the authoritative task state.

This preserves the current authority model:

- the queue is for discovery,
- the task card is for truth,
- and execution or resume begins only after the authoritative artifact is read.

## Queue trust rules

The startup flow only works if the queue is trustworthy enough to use.

The queue should therefore follow these rules:

- `docs/harness/indexes/active-tasks.md` remains derivative, never authoritative.
- Every queue entry must correspond to a real authoritative task card.
- Queue membership and queue state summaries must match the task cards they summarize.
- If the queue contains entries that do not correspond to real task cards, the queue should be treated as stale.
- If task cards exist but the queue is empty, incomplete, or obviously outdated, that should be treated as a harness-maintenance problem rather than normal operating ambiguity.

The fallback rule should be explicit:

- queue first for discovery,
- authoritative task cards win on any mismatch,
- direct scan of authoritative task cards is the fallback only when the queue is missing or untrustworthy.

That fallback keeps the queue useful without making it a second source of truth.

## Executable-by-default queue semantics

For startup selection, the default queue should answer a narrow operational question:

"What can a coding agent execute now?"

That means the default startup queue should show executable tasks only.

Recommended default inclusion:

- `active`
- `validating` only when the intended next action is validation or evidence-generation work

Recommended default exclusion:

- `draft`
- `checkpoint`
- `blocked`
- `awaiting_approval`
- `complete`
- `cancelled`

Those excluded states may still belong in other derivative views or clearly separated sections, but they should not be mixed into the default "to implement now" queue.

## Follow-up surfaces to align

This context note implies follow-up edits across the harness.

### `docs/harness/README.md`

Add the startup discovery path for a fresh agent:

- start from the active executable-task queue,
- then open the authoritative task card,
- then move into execution or resume as appropriate.

### `docs/harness/AGENTS.md`

Add a direct rule for search and selection at startup:

- use the active-task queue first,
- fall back to authoritative task-card scanning only when the queue is stale, absent, or inconsistent.

### `docs/harness/indexes/active-tasks.md`

Tighten the semantics of the file so it acts as the executable-work discovery surface rather than a mixed-status live dump.

That includes:

- requiring correspondence to real task cards,
- clarifying which states belong in the default queue,
- and separating non-executable items into distinct sections or separate views.

### `docs/harness/workflows/task-execution-loop.md`

Clarify that execution begins after task selection, not before. The workflow should stay focused on execution from an already selected authoritative card, but it should acknowledge the startup handoff from the discovery queue.

### `docs/harness/workflows/handoff-resume-loop.md`

Clarify how a fresh agent reaches a resumable item when no target has been preselected. The loop should continue to require authoritative-card-first behavior after selection.

### `docs/harness/prompts/execution-agent.md` and `docs/harness/prompts/resume-agent.md`

Adjust the prompt framing so it no longer silently assumes the target task is already known in every fresh-session entry case.

The prompts do not need to absorb queue semantics fully, but they should be consistent with the startup flow defined elsewhere.

## Non-goals

This note does not propose:

- a redesign of Layers A through D,
- a new artifact type,
- a machine-readable synchronization system,
- a full harness-wide workflow rewrite,
- or a broad overhaul of intake, execution, and resume semantics beyond the startup-discovery gap.

The purpose is narrower: make it possible for a fresh coding agent to find and select the next executable task without guessing.

## Expected outcome

After the follow-up changes implied by this note, another agent should be able to:

1. enter the harness,
2. inspect one trustworthy executable-task queue,
3. select a task from that queue,
4. open the authoritative task card,
5. and begin the correct execution or resume loop without ambiguity about what is live, executable, or authoritative.
