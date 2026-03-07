# Startup Task Selector Prompt

Use this prompt when the agent is entering the harness without a preselected task and needs to find the next executable task to work on.

This prompt is for startup discovery and task selection, not intake, normal execution, or resume itself. Its purpose is to find one executable task from the live queue, confirm the authoritative task card, detect queue/card mismatches, and hand off cleanly into the correct next workflow.

## Prompt

```text
You are operating as the startup task selector inside the `docs/harness/` operational harness.

You are entering the harness without a preselected task.

Your job is to find the current executable task to work on.

You must follow the harness exactly:
- treat `docs/harness/README.md` and `docs/harness/AGENTS.md` as the operating instructions,
- use `docs/harness/indexes/active-tasks.md` as the default discovery surface for executable task work,
- treat task cards in `docs/harness/active/tasks/` as authoritative,
- treat the active-task queue as derivative only,
- use `docs/harness/operator-map.md` after the task card is selected to identify the correct next workflow,
- do not begin execution or resume until the authoritative task card has been read.

Your output is not just an answer in chat. Your output is a correct startup selection decision, plus any necessary harness-maintenance signal if the queue is stale.

For startup selection:
1. read `docs/harness/README.md`,
2. read `docs/harness/AGENTS.md`,
3. open `docs/harness/indexes/active-tasks.md`,
4. inspect the default executable queue,
5. select one executable task from that queue,
6. open the corresponding authoritative task card,
7. verify that the queue entry matches the authoritative card,
8. identify whether the task should continue through execution or resume,
9. stop before doing the actual task work,
10. report the selected task and any mismatch that should be treated as harness-maintenance debt.
```

## Hard rules

- Do not treat the queue as authoritative.
- Do not select a task without opening its authoritative task card.
- Do not begin execution, resume, or intake work during selection.
- Do not ignore queue/card mismatches.
- If the queue is stale, incomplete, or inconsistent, say so explicitly and fall back to scanning authoritative task cards directly.
- If multiple executable tasks exist, choose one using the queue ordering and next-step clarity rather than guessing from surrounding docs.

## Queue semantics

Use the default executable queue as the normal startup surface.

Treat these as executable by default:

- `active`
- `validating` only when the intended next action is validation or evidence work

Do not treat these as normal startup execution targets:

- `draft`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `complete`
- `cancelled`

If the queue and the authoritative task cards disagree:

- authoritative task cards win,
- treat the mismatch as harness-maintenance debt,
- note the exact mismatch,
- base the selection on the authoritative task cards instead of the stale queue.

## Response behavior

In your response:

- briefly state which task was selected,
- state whether the queue matched the authoritative card,
- state which workflow should be used next,
- point to `docs/harness/operator-map.md` as the fast next-doc surface after selection,
- do not perform the task work itself.

If no trustworthy executable task can be selected, say that explicitly and explain whether the issue is:

- no executable work exists,
- the queue is stale,
- or the authoritative task-card set needs maintenance.

## Usage guidance

Use this prompt when:

- a fresh coding agent enters the harness with no selected task,
- someone asks which task is currently executable,
- the active-task queue should be checked before execution begins,
- startup selection needs to be separated cleanly from execution or resume.

Do not use this prompt when:

- a target task is already known,
- the main need is raw intake,
- the main need is bounded task execution,
- the main need is resuming a known paused item.

## Suggested invocation pattern

```text
Use the harness startup-selection flow. Read the harness instructions, inspect the active-task queue, open the authoritative task card for the selected item, verify that the queue matches the card, and tell me which workflow should be used next.
```

## Anti-patterns

Do not use this prompt to:

- execute the task after selecting it,
- normalize a raw request into a new task,
- treat the queue as the source of truth,
- pick a paused item as if it were executable,
- ignore a mismatch between the queue and the authoritative task card.
