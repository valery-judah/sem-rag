# Harness navigation and surface-reduction proposals

## Context

The harness is already materially better than many long-lived agent workflow systems:

- the layered model is coherent,
- the startup route is explicit,
- task cards are authoritative,
- the active-task queue is clearly derivative,
- and the Layer B / Layer C / Layer D split is much cleaner than the older mixed vocabulary.

The remaining friction is less about the model and more about the reading path through the model.

In practice, answering a simple operational question such as:

- what does this current mode mean,
- what workflow should I use next,
- or which document is the normative one for this exact decision

still requires opening several files and reconstructing the intended sequence.

The problem is not lack of documentation. The problem is that the harness currently distributes the shortest usable answer across too many surfaces.

## Current problem

### 1. Mode lookup still takes too many hops

For a live task, the path to mode-specific guidance is currently:

1. open the task card,
2. identify `layer_b.current_mode`,
3. know that Layer B semantics live in `concepts/`,
4. know that routing policy lives in `policies/`,
5. know that detailed mode guidance lives in `concepts/layer-b-modes/`,
6. open the correct mode file.

This is all logically consistent, but it is heavier than it should be for a common operational action.

### 2. Workflow selection knowledge is spread across multiple entry surfaces

The same basic routing guidance appears in:

- `docs/harness/README.md`,
- `docs/harness/AGENTS.md`,
- prompt files,
- workflow introductions,
- and policy docs.

That improves redundancy, but it also increases maintenance burden and creates more places where small wording drift can reintroduce ambiguity.

### 3. The harness has strong semantics but a weak "fast path"

The docs are good at explaining the system in full, but weaker at giving a compact operator answer to:

- I know the task card.
- I know the current mode.
- I know the current state.
- What exact document should I read next?

That fast path should be nearly trivial.

### 4. Task cards know the current mode and state but do not help the reader navigate from them

The card records the truth correctly:

- one current mode,
- one current state,
- one current next step.

But the card does not currently help the next reader jump directly from:

- `current_mode` -> the detailed mode file
- `state` -> the workflow or control-handling doc most likely needed

That means even authoritative cards still require external harness literacy for efficient use.

### 5. Prompt docs repeat a lot of operator guidance that is already canonical elsewhere

The prompt files are useful, but they currently restate large chunks of harness behavior in full prose.

That has two downsides:

- maintainers must keep more text aligned across files,
- and agents reading prompts may see overlapping instruction surfaces that differ slightly in tone or emphasis.

The issue is not that the prompt docs are wrong. The issue is that they may be carrying too much duplicated operational payload.

## Proposal

### Proposal A. Add one compact "what to open next" operator map

Add a small operator-facing reference page, for example:

- `docs/harness/operator-map.md`

Its job would be narrow:

- if you know the task card and need the current mode meaning, open this
- if you know the state and need the next workflow, open this
- if you need the routing rule, open this
- if you need review/approval/handoff handling, open this

This file should not restate the full harness. It should be a short jump table.

Suggested shape:

- `If you know the current task and want to work now -> workflows/task-execution-loop.md`
- `If the card is paused at checkpoint -> workflows/checkpoint-review-loop.md`
- `If the item is being resumed -> workflows/handoff-resume-loop.md`
- `If you need to validate or repair the mode -> policies/routing-rules.md`
- `If you need mode-specific operating guidance -> concepts/layer-b-modes/<mode>.md`

This gives the harness a true fast path instead of making the user reconstruct it from multiple broader docs.

### Proposal B. Add direct navigation guidance to the task-card template

The task-card template should grow a tiny operator-navigation block, not a large new schema surface.

Possible shape:

- a short prose note in the template saying that the card should make it easy to jump from:
  - `layer_b.current_mode` to the relevant mode file
  - `layer_d.state` to the relevant workflow or control loop

This does not require dynamic links in frontmatter.

It can be done with:

- a standard "operator notes" section,
- or template guidance telling authors to include explicit references in the summary when the next workflow is not obvious.

The goal is that authoritative cards become easier to use directly, especially for fresh or resumed agents.

### Proposal C. Reduce repeated routing prose across README, AGENTS, and prompts

The harness should keep one canonical concise statement of:

- startup path,
- workflow selection path,
- and write-back boundary.

Then other docs should point to that statement instead of re-explaining it in full.

This does not mean removing all redundancy. It means reducing full-prose duplication where duplication is not adding distinct value.

Recommended direction:

- `README.md` remains the entry-and-orientation surface,
- `AGENTS.md` remains the direct execution contract,
- prompts become thinner invocation wrappers around those two plus the target workflow.

This would lower alignment cost and make future harness edits less drift-prone.

### Proposal D. Add a state-to-workflow lookup table

The current docs explain Layer D well, but the practical lookup from state to workflow is still more diffuse than necessary.

Add one compact table, likely in `README.md` or the proposed operator map:

| State | Default action | Primary doc |
|---|---|---|
| `active` | execute current slice | `workflows/task-execution-loop.md` |
| `validating` | run validation/evidence cycle | `workflows/task-execution-loop.md` |
| `checkpoint` | stop normal execution; review boundary | `workflows/checkpoint-review-loop.md` |
| `awaiting_approval` | stop and preserve approval dependency | `workflows/checkpoint-review-loop.md` or approval packet path |
| `blocked` | stop and preserve blocker truth | relevant task/workstream artifact plus blocker handling guidance |
| `draft` | finish shaping into actionable task | `workflows/intake-loop.md` or task-shaping path |

The harness already implies this. The proposal is to make the lookup immediate.

### Proposal E. Make mode discovery easier from the Layer B surfaces

The Layer B docs are good, but they can become easier to use operationally.

Recommended improvements:

- add a very short "If your task card already says `current_mode=X`, open `Y` now" note near the top of `concepts/layer-b-modes/README.md`
- consider adding a one-line "common next doc" pointer inside each mode file:
  - use routing rules if mode fit is unclear
  - use task execution loop if mode is confirmed and state permits execution

This keeps the mode files mode-specific while reducing the need to infer the next navigation step.

## Suggested implementation order

1. Add the compact operator map.
2. Add the state-to-workflow lookup table.
3. Thin prompt docs where they restate already-canonical routing prose.
4. Add template guidance so task cards become stronger navigation surfaces.
5. Recheck startup, execution, and resume paths using a fresh-agent walkthrough.

This order improves practical usability first, then reduces maintenance burden.

## Non-goals

This proposal should not:

- change the layered model,
- add new Layer B modes,
- change Layer D states,
- introduce a new artifact type for live work,
- replace authoritative task cards with a generated UI,
- or turn prompts into the primary source of truth.

The goal is not a new workflow system. The goal is to make the existing system faster to enter and harder to misuse.

## Expected outcome

After these changes, the harness should feel simpler in practice without becoming simpler in concept.

The expected result is:

- fewer document hops to find mode instructions,
- clearer state-to-workflow routing,
- less duplicated prose to keep aligned,
- stronger task-card usability as an operator surface,
- and lower cognitive load for fresh or resumed agents.

The harness already has a solid model. The next improvement is to make the shortest correct reading path more obvious than the longer reconstructive one.
