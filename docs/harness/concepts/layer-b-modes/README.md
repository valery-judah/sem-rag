# Layer B Operating Modes

This directory contains the detailed specifications for the atomic operating modes defined in Layer B of the agentic work model.

Layer B defines the current working posture for an agent. It answers the question: *How should the agent behave now?*

These modes are current-state routing conclusions derived from Layer A classification, not permanent task identities. A task may transition through multiple modes as work progresses.

## Available Modes

1. [Research Scout](./research-scout.md): Reduce uncertainty, gather evidence, compare options, and synthesize findings when the dominant problem is still exploratory.
2. [Contract Builder](./contract-builder.md): Transform a partly known problem into an implementation-ready contract.
3. [Routine Implementer](./routine-implementer.md): Execute a clear, bounded, implementation-ready change with normal engineering discipline.
4. [Refactor Surgeon](./refactor-surgeon.md): Perform behavior-preserving structural change with deliberate control over code shape and regression risk.
5. [Debug Investigator](./debug-investigator.md): Diagnose known failing behavior when the root cause is not yet isolated.
6. [Migration Operator](./migration-operator.md): Execute or prepare rollout-sensitive transitions where sequencing, compatibility, reversibility, and operational safety matter.
7. [Optimization Tuner](./optimization-tuner.md): Improve measurable performance, efficiency, latency, throughput, resource usage, or cost when tuning rather than raw implementation dominates.
8. [Quality Evaluator](./quality-evaluator.md): Produce or interpret evidence about output quality when correctness cannot be established by ordinary tests alone.

# Layer B Modes

This directory contains the detailed operational references for the canonical atomic operating modes defined by Layer B.

Use these files when you already know that Layer B is the relevant layer and you need mode-specific guidance for how an agent should operate on the current slice.

## What Layer B does

Layer B defines the **current atomic operating mode** for a task slice.

It answers the question:

> How should the agent work now?

Layer B is about present operating posture, not permanent identity, not lifecycle state, and not long-horizon workstream structure.

A task may pass through multiple Layer B modes over time as the shape of the work changes.

## What this directory is for

This directory exists to keep the detailed mode guidance separate from the higher-level Layer B architecture document.

Use the files here when you need:
- mode-specific behavioral guidance,
- a sharper definition of when a mode does or does not apply,
- typical outputs for a mode,
- common reroute triggers,
- operational risks or failure modes specific to one mode.

Keep the architectural meaning of Layer B in:
- `docs/harness/concepts/layer-b-operating-modes.md`

Keep the routing policy that maps task slices into one current mode in:
- `docs/harness/policies/routing-rules.md`

## How to use these mode files

For a real task slice, the recommended order is:

1. Determine the current slice.
2. Read the Layer A snapshot or fill the Layer A core.
3. Use the routing rules to choose one current Layer B mode.
4. Read the corresponding mode file in this directory.
5. Apply the mode guidance while keeping Layer C and Layer D separate.

If no single mode fits cleanly, the task is usually too broad and should be resliced rather than forced into a blended mode.

## Canonical modes

The following mode files are the canonical detailed references for Layer B.

| Mode | Purpose | Detailed file |
|---|---|---|
| Research Scout | Reduce uncertainty through discovery, mapping, and evidence gathering when the main problem is still exploratory. | `research-scout.md` |
| Contract Builder | Turn a partly known problem into an explicit contract, boundary, schema, or acceptance target that downstream work can execute against. | `contract-builder.md` |
| Routine Implementer | Execute a clear, bounded change when the implementation path is already sufficiently defined. | `routine-implementer.md` |
| Refactor Surgeon | Perform behavior-preserving structural change with explicit control over regression risk. | `refactor-surgeon.md` |
| Debug Investigator | Diagnose failing or incorrect behavior when the root cause is not yet isolated. | `debug-investigator.md` |
| Migration Operator | Handle staged transitions where sequencing, compatibility, rollback, and operational safety dominate. | `migration-operator.md` |
| Optimization Tuner | Improve measurable system behavior when tuning and comparison against metrics dominate. | `optimization-tuner.md` |
| Quality Evaluator | Generate or interpret evidence about quality, correctness, readiness, or acceptance when ordinary implementation alone is not enough. | `quality-evaluator.md` |

## Important boundaries

When reading or applying these files, keep these distinctions explicit.

### Layer B is not Layer A

Layer A describes the current shape of the slice.

Layer B describes the current operating posture selected from that shape.

### Layer B is not Layer C

Layer C adds overlays and containers such as:
- `review_gatekeeper`
- `governance_escalation`
- `feature_cell`

Those constructs may constrain or wrap work done in a Layer B mode, but they are not modes themselves.

### Layer B is not Layer D

Layer D describes lifecycle control state such as:
- `active`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`

A task can remain in the same Layer B mode while Layer D changes, or remain in the same Layer D state while Layer B changes.

## How these files should evolve

These mode files are allowed to become more operational over time than the umbrella Layer B document.

They may eventually include:
- sharper “when to use / when not to use” guidance,
- typical output patterns,
- mode-specific anti-patterns,
- common reroute signatures,
- more concrete examples,
- lightweight operational checklists.

What should remain stable is the canonical set of modes and the rule that a task slice should have exactly one current Layer B mode at a time.

## Recommended reading path

If you are entering Layer B fresh:

1. Read `docs/harness/concepts/layer-b-operating-modes.md`.
2. Read `docs/harness/policies/routing-rules.md`.
3. Open the relevant detailed mode file in this directory.

If you are already operating on a task:

1. Read the authoritative task card.
2. Confirm the current slice.
3. Confirm or repair the current mode using the routing rules.
4. Read the detailed mode file for the selected mode.

## Practical rule

Use this directory for **mode-specific depth**, not for general harness workflow or lifecycle control.

If you need to know:
- how to route a slice, use the routing rules,
- how to operate within a mode, use the relevant mode file here,
- how to handle review, handoff, or workstream coordination, use the workflow documents,
- how to interpret current status, use Layer D.