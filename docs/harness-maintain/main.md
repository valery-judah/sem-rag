# Harness Maintenance And Evolution Guide

This document is for maintainers changing the harness itself.

Use it when you are:
- changing harness ontology or public vocabulary,
- editing templates, workflows, prompts, or example artifacts,
- deciding whether a new mode, state, preset, or artifact type is justified,
- migrating compatibility layers,
- or introducing machine-readable validation.

Use `README.md` and `AGENTS.md` for day-to-day operation. Use this file for harness evolution policy.

`docs/harness/operator-map.md` is the fast routing surface for known task cards. Keep it short, operator-facing, and free of workflow-procedure prose.

## Recommended maintainer reading path

When maintaining or extending the harness, read in this order:

1. `docs/harness/README.md`
2. `docs/harness/concepts/operational-playbook.md`
3. the layer references in `docs/harness/concepts/`
4. the five workflow documents in `docs/harness/workflows/`
5. the templates in `docs/harness/templates/`
6. `docs/harness/policies/routing-rules.md`
7. this file while deciding what to change and what else must stay aligned

## What this guide owns

This file is the primary home for:
- harness-wide invariants and non-goals,
- change thresholds for Layer B, Layer C, Layer D, and artifact surfaces,
- compatibility and migration policy,
- cross-file synchronization rules,
- validation expectations after a harness change,
- and deferred automation / placeholder status.

Operator-facing usage should stay in workflows, templates, prompts, and examples. Those docs may contain short local maintenance rules, but they should point back here for harness-wide evolution policy.

## Core invariants

Keep these stable unless there is a deliberate redesign:

- The harness operates on current slices of work, not vague initiatives.
- Layer A classifies the slice, Layer B picks one current mode, Layer C adds wrapper/control context, and Layer D records lifecycle control status.
- Task cards and workstream cards are the authoritative operational records.
- Handoff notes, indexes, packets, and examples are secondary artifacts.
- The harness should remain small, readable, and easy to resume.
- Better slicing is preferred over inventing new universal taxonomy.

## Change policy

### Layer A

The Layer A taxonomy should remain compact and routing-relevant.

Keep the current required core small. Promote optional fields to required only when they repeatedly change routing or control decisions in real work.

Add a new Layer A axis or stable value only when:
- repeated real slices cannot be classified cleanly with the existing model,
- the distinction affects downstream routing or control materially,
- operators can apply it consistently,
- and the result improves clarity more than it increases taxonomy churn.

Do not let Layer A absorb:
- Layer B modes,
- Layer C constructs or presets,
- or Layer D state semantics.

### Layer B

The canonical Layer B mode set should stay small.

Add a new mode only when:
- repeated real slices cannot be routed cleanly with the existing set,
- the distinction changes operating posture materially,
- the mode can be applied consistently by different operators,
- and the new mode improves routing clarity more than it increases ambiguity.

When a Layer B mode changes:
- update the Layer B concept docs,
- update `policies/routing-rules.md`,
- update task-facing templates or prompts that enumerate allowed modes,
- update examples that demonstrate affected routing,
- and update any future machine-readable catalogs.

The mode files under `concepts/layer-b-modes/` should follow one shared authoring contract. Keep them aligned on:
- purpose,
- when to use,
- typical Layer A signals,
- primary working posture,
- primary outputs,
- allowed autonomy pattern,
- typical validation style,
- common reroute triggers,
- common next modes,
- and typical risks / failure modes.

Prefer routing policy over inventing a hard universal workflow FSM.

### Layer C

The canonical Layer C model is:
- `feature_cell`
- `control_profile`

The preset set should also remain small:
- `baseline`
- `reviewed`
- `change_controlled`
- `high_assurance`

Add a new construct or preset only when normalized fields and existing presets cannot express repeated real control needs without confusion.

Do not let Layer C changes blur into Layer D state semantics or Layer B routing.

Live harness guidance should use canonical Layer C terms:
- `feature_cell`
- `control_profile`
- preset aliases such as `reviewed`, `change_controlled`, and `high_assurance`

Legacy overlay-era labels are compatibility terms only. They may still appear in card frontmatter or historical notes, but live docs should not teach them as active canonical constructs.

When Layer C changes:
- update `docs/harness/concepts/layer-c/`,
- update compatibility notes and migration guidance,
- update workflows, prompts, and templates that mention current Layer C representation,
- update examples that demonstrate the current shape,
- and keep `concepts/layer-c-overlays-containers.md` historical rather than concurrent.

### Layer D

The canonical Layer D state set should stay at the current eight universal states unless there is strong evidence otherwise.

Add a new universal state only when:
- the distinction appears repeatedly across workflows,
- it changes control behavior materially,
- existing states plus `phase` cannot model it clearly,
- operators can apply it consistently,
- and the result improves cross-workflow clarity.

When Layer D changes:
- update `concepts/layer-d/README.md`, `concepts/layer-d/states.md`, `concepts/layer-d/schema.md`, and `concepts/layer-d/scope-and-transitions.md` as needed,
- update workflows and prompts that gate execution by state,
- update templates and examples that enumerate allowed states,
- update indexes that summarize state,
- and update future schemas or registries.

### Artifacts And Indexes

Prefer improving the existing small artifact set over creating new artifact classes.

Add a new artifact type, index, or registry only when it does one of:
- materially improves resumability,
- materially improves control-legibility,
- materially reduces operator ambiguity,
- or provides machine validation that the prose model cannot supply reliably.

Do not add artifacts that merely restate authoritative cards in another place.

The operator map is the exception only in the narrow sense that it is a jump table rather than a second source of truth. It should point to the canonical docs, not restate them in full.

Keep the operational playbook task-first by default. Add workflow burden, artifact types, or machine-readable enforcement only when they improve resumability or control clarity in real use.

## Current compatibility status

### Layer C historical shorthand

The canonical Layer C model is v2 and lives in `docs/harness/concepts/layer-c/`.

Live task and workstream templates now use canonical Layer C fields directly. Legacy shorthand such as:
- `container: feature_cell`
- `overlays: []`
- overlay-era labels such as `review_gatekeeper`

belongs only in historical notes, older artifacts, or explicit compatibility references.

Do not teach that shorthand as current card-authoring practice.

### Historical Layer C reference

`docs/harness/concepts/layer-c-overlays-containers.md` is a superseded historical pointer only.

Maintain it as:
- a brief historical explanation,
- a mapping reference for older terms,
- and a pointer back to the current v2 docs.

Do not let it grow into a second current Layer C authority.

### Machine-readable files

The following files currently exist as reserved placeholders, not implemented contracts:
- `docs/harness/schemas/*.json`
- `docs/harness/registries/*.json`

At the time of this guide, those files are effectively empty (`{}`).

Do not treat them as authoritative until they are deliberately implemented and wired into validation.

### Indexes

Indexes are derivative operating summaries, not the source of truth.

They are healthy when:
- they are shorter than the underlying authoritative cards,
- their state/mode summaries match the cards,
- and every concrete entry corresponds to a real authoritative artifact.

If an index contains concrete entries, it should be treated as a live maintained view rather than an illustrative placeholder.

For startup discovery, `docs/harness/indexes/active-tasks.md` should function as the executable-task queue. If it is stale or incomplete, repair it or fall back to authoritative task cards directly.

## Synchronization matrix

Use this matrix whenever you change a harness surface.

### If you change Layer B

Synchronize:
- `docs/harness/concepts/layer-b-operating-modes.md`
- `docs/harness/concepts/layer-b-modes/`
- `docs/harness/policies/routing-rules.md`
- templates, prompts, and examples that enumerate allowed modes
- future registries or schemas that represent modes

### If you change Layer C

Synchronize:
- `docs/harness/concepts/layer-c/`
- compatibility notes in templates, prompts, workflows, and examples
- `docs/harness/concepts/layer-c-overlays-containers.md`
- any machine-readable representation once implemented

### If you change Layer D

Synchronize:
- `docs/harness/concepts/layer-d/README.md`
- `docs/harness/concepts/layer-d/states.md`
- `docs/harness/concepts/layer-d/schema.md`
- `docs/harness/concepts/layer-d/scope-and-transitions.md`
- execution, review, resume, and workstream workflows
- prompts that gate action by state
- templates and examples that enumerate states or companion fields
- indexes and future schemas/registries

### If you change templates

Synchronize:
- filled examples that demonstrate those templates
- prompts and workflows that assume the old artifact shape
- any future schema files for those artifacts

### If you change startup or routing surfaces

Synchronize:
- `docs/harness/README.md`
- `docs/harness/AGENTS.md`
- `docs/harness/operator-map.md`
- any prompts that point agents into the harness
- any workflows whose entry assumptions changed

### If you change workflows or prompts

Synchronize:
- the corresponding operator-facing guidance in `README.md` or `AGENTS.md` when affected
- `docs/harness/operator-map.md` when the fast path or state-to-workflow lookup changed
- any template fields or examples referenced by the workflow
- layer concept docs if the workflow started teaching ontology instead of consuming it

## Validation checklist

After a harness change:

1. Check vocabulary consistency with `rg`.
   Review terms like `feature_cell`, `control_profile`, `checkpoint`, `awaiting_approval`, `review_gatekeeper`, `governance_escalation`, `overlay`, `overlays`, and `container`.

2. Verify remaining legacy terms are intentional.
   They should be either explicit compatibility references or historical notes, not accidental live ontology.

3. Spot-check one workflow, one prompt, one template, and one example.
   Confirm they teach the same Layer B, Layer C, and Layer D boundaries.

4. Walk the fresh-agent startup path.
   Confirm `README.md` -> `AGENTS.md` -> `indexes/active-tasks.md` -> authoritative task card -> `operator-map.md` -> next workflow still works without guesswork.

5. Walk the known-task operator path.
   Confirm a reader with only `layer_b.current_mode` and `layer_d.state` can reach the right mode file and workflow from the task card plus `operator-map.md`.

6. Confirm authoritative-vs-derivative boundaries remain clear.
   Task/workstream cards must still be primary; indexes and handoff notes must remain secondary.

7. If machine-readable files were changed, verify they now reflect the prose contract rather than placeholder state.

## Deferred work

The harness intentionally does not yet require:
- machine-enforced schemas,
- automatic linting,
- dashboard generation,
- or heavyweight orchestration.

That can change later, but only after the prose operating model is stable enough that automation is enforcing settled rules rather than freezing churn.

Good next steps for future maintainers are:
- implement real JSON schemas only after the markdown artifact shape is stable,
- keep reducing remaining historical Layer C shorthand references,
- decide whether currently empty indexes should become maintained summaries or be removed,
- and keep reducing duplicated compatibility notes when the underlying migration is complete.
