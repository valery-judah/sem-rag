# Harness artifact update discipline and agent push signals

## Context

This note was produced while executing a real harness task and deciding whether the current task card was sufficient as the authoritative artifact for the work.

The answer was yes at the artifact-model level: the harness already has the right primary artifact for this class of work. The friction appeared elsewhere. The harness clearly says the task card is authoritative, but the execution flow does not push strongly enough toward updating it before the agent moves on, reports progress, pauses, reroutes, or closes a cycle.

This proposal is therefore about execution discipline, not artifact proliferation.

## Current problem

The main issue is diffuse obligation combined with a weak forcing function.

The harness already contains many correct statements such as:

- keep authoritative artifacts current,
- leave a concrete `next_step`,
- update the task card before pausing or handing off,
- reflect truthful Layer D state,
- and record work log / evidence / decision context when it materially changes.

The problem is that those expectations are spread across:

- `docs/harness/README.md`,
- `docs/harness/AGENTS.md`,
- `docs/harness/workflows/task-execution-loop.md`,
- prompts,
- templates,
- and supporting concept docs.

Because the obligation is distributed and partly phrased as general discipline rather than as a hard end-of-step rule, an agent can still:

- do meaningful work,
- discover a reroute,
- form a new `next_step`,
- or reach a state boundary,

and only later remember that the task card should probably be updated.

That means the harness is explicit about the importance of authoritative artifacts in principle, but less forceful about update timing in practice.

## Why this matters

This gap matters because it weakens the exact property the harness is trying to preserve: operational truth living in the authoritative artifact rather than in transient chat or final-response prose.

When write-back discipline is weak:

- the final response can become more current than the task card,
- resumability degrades because the next agent must reconstruct what changed,
- Layer B reroutes and Layer D transitions can be under-recorded,
- evidence and decision references can lag behind the actual work,
- and the task card drifts toward "eventually updated" instead of "operationally current."

That is a harness-level problem, not merely a local style issue.

## Specific friction points in the current harness

### 1. Update rules are present but not sequenced tightly enough

The harness repeatedly says to keep the authoritative artifact current, but it does not always present that update as a mandatory boundary immediately after meaningful work and before reporting.

The result is that the write-back step feels important but postponable.

### 2. Execution guidance emphasizes reading truth more than writing truth back

The current execution loop strongly reinforces:

- read the task card first,
- respect Layer D,
- execute the bounded slice,
- and reassess routing/control.

That is good, but the mirrored behavioral rule should be equally strong:

- once work changes the truth, write the truth back before you conclude the cycle.

That second half is present, but less forcefully.

### 3. Finalization boundaries are not explicitly tied to artifact refresh

The docs make it clear that the task card should stay authoritative, but they do not strongly enough state that:

- pause,
- handoff,
- reroute,
- checkpoint,
- validation closeout,
- and final reporting

should all happen only after the authoritative artifact has been refreshed.

Without that sequencing rule, agents can treat the final message as the natural place to summarize the truth they have not yet written back.

### 4. State-transition companion fields are easy to under-update

The harness correctly defines companion fields such as:

- `blocking_reason`
- `unblock_condition`
- `checkpoint_reason`
- `approval_ref`
- `evidence_refs`
- `decision_ref`

But the current flow still allows state changes to feel primary and companion updates to feel secondary. In practice, that makes partial state updates too easy.

### 5. Prompts do not strongly enough force stale-field checks before completion

The current prompts help an agent enter the right workflow and respect state boundaries, but they do not consistently force a last-pass question such as:

- is the recorded `next_step` stale,
- is the work log missing the latest step,
- does the current mode still match,
- does Layer D still match reality,
- and are the new references linked?

That means the behavioral nudge exists, but the push is still weaker than it should be.

## Proposal

### Proposal A. Add a single write-back invariant

Add one compact harness-wide invariant:

> After meaningful progress, update the authoritative artifact before reporting, pausing, rerouting, or closing the cycle.

This should be short enough to repeat across README, AGENTS, workflows, and prompts without creating redundancy overload.

### Proposal B. Add a named write-back boundary to the task execution loop

The task execution loop should include an explicit write-back boundary after meaningful work and before cycle closeout.

That step should say, in direct operational terms:

- refresh the task card,
- update `next_step` or terminal/paused state,
- record mode/state changes,
- link evidence or decisions,
- then report or stop.

This gives the execution loop a stronger behavioral cadence:

work -> update card -> then report.

### Proposal C. Add push-language to AGENTS and prompts

`AGENTS.md` and the execution/resume prompts should use short imperative language rather than soft reminders.

The goal is not more text. The goal is stronger behavioral pull.

Examples:

- update the authoritative artifact before you stop,
- do not let the final response become more current than the task card,
- if work changed the truth, write the truth back first.

### Proposal D. Strengthen task-card template guidance

The task-card template should more explicitly treat several fields as required maintenance surfaces whenever meaningful progress occurs:

- `layer_b.current_mode` when rerouted,
- `layer_d.state`,
- `layer_d.next_step`,
- `layer_d_companion.*` fields relevant to the current boundary,
- work log,
- evidence or decision references when produced.

This should be framed as operational maintenance guidance, not as passive description of available fields.

### Proposal E. Tie Layer D transitions to required companion updates

The harness should make partial state updates feel operationally incomplete.

Recommended coupling rules:

- `blocked` requires `blocking_reason` and `unblock_condition`
- `checkpoint` requires `checkpoint_reason` and linked review packet when available
- `awaiting_approval` should point to an approval artifact or explicit approval dependency
- `validating` should accumulate evidence references
- `complete` should record a concrete acceptance basis

The current model already supports this. The proposal is to make the behavioral requirement more explicit.

## Recommended follow-up surfaces

The most important follow-up surfaces are:

- `docs/harness/AGENTS.md`
- `docs/harness/workflows/task-execution-loop.md`
- `docs/harness/prompts/execution-agent.md`
- `docs/harness/prompts/resume-agent.md`
- `docs/harness/templates/task-card.template.md`

Optionally, add a short top-level version of the invariant to:

- `docs/harness/README.md`

so the discipline is visible at entry.

## Suggested language patterns

The future implementation can reuse compact phrases like:

- `Before you pause, report, reroute, or close, refresh the authoritative artifact.`
- `Do not let the final response become more current than the task card.`
- `If work changed the truth, write the truth back before anything else.`
- `State changes are incomplete until the required companion fields are updated.`
- `Work log, next_step, and control state should reflect the latest meaningful step before the cycle ends.`

## Reasoning

The goal is not to add more process or more artifact types.

The harness already has the right core model:

- authoritative task/workstream artifacts,
- one current mode,
- truthful Layer D,
- concrete `next_step`,
- and optional supporting packets when boundaries become real.

What is missing is a stronger execution-time discipline that pushes the agent to refresh that model at the right moment.

This is a low-cost change with high leverage. It does not require schema enforcement, automation, or a workflow engine. It only requires clearer sequencing and stronger imperative guidance at the points where agents naturally decide whether they are "done for now."

## Expected outcome

After the implied follow-up changes, an agent should feel a stronger default pull toward:

- updating the task card immediately after meaningful work,
- refreshing `next_step`,
- recording reroutes and Layer D transitions,
- linking evidence or decision artifacts when they become real,
- and treating the final response as downstream of artifact refresh rather than as compensation for a stale card.

The intended result is simple:

- the authoritative artifact stays more current,
- resumability improves,
- and the harness more reliably behaves as an operational system rather than a retrospective note system.
