# Harness-Wide Layer C Alignment: Next-Thread Prompt

Use the prompt below to start a fresh thread with compact context.

````md
You are working in this repository:

`/Users/val/projects/rag/sem-rag`

Your task is to perform a **harness-wide Layer C alignment pass** so the broader `docs/harness/` doc set matches the current Layer C v2 model already established under:

- `docs/harness/concepts/layer-c/README.md`
- `docs/harness/concepts/layer-c/control-profiles.md`
- `docs/harness/concepts/layer-c/feature-cell.md`
- `docs/harness/concepts/layer-c/presets.md`
- `docs/harness/concepts/layer-c/schema.md`
- `docs/harness/concepts/layer-c/examples.md`

## Current context

The Layer C v2 mini-spec is already internally aligned.

The key decisions already made are:

- canonical container: `feature_cell`
- canonical control object: `control_profile`
- preset aliases only:
  - `baseline`
  - `reviewed`
  - `change_controlled`
  - `high_assurance`
- baseline is **implicit by default**
  - use `control_profiles: []` when no explicit Layer C control burden is materialized
- canonical bundle shape is:

```yaml
layer_c:
  feature_cell: <feature_cell | null>
  control_profiles:
    - <control_profile>
```

- presets are ergonomic summaries
- normalized fields are authoritative
- inheritance fields are workstream-only
- trigger classes are shared starter registries, not permanently closed enums
- the old `docs/harness/concepts/layer-c-overlays-containers.md` is now historical background, not the primary Layer C reference

Also note:

- `docs/harness/README.md` has already been updated to point the main concepts map at the new `concepts/layer-c/` directory
- the remaining inconsistency is in the broader harness docs: AGENTS, workflows, templates, prompts, examples, and adjacent concept docs still contain overlay-era language or artifact conventions

## Objective

Align the rest of the harness to the Layer C v2 model without turning this into a greenfield redesign.

This should be a **conservative but thorough consistency pass**:

- aggressive about terminology cleanup
- conservative about changing artifact schemas unless needed
- explicit about compatibility where full migration is too large

## Main goals

1. **Normalize Layer C vocabulary across the harness**
   - replace overlay-first language with the v2 model where appropriate
   - make sure the live vocabulary centers on:
     - `feature_cell`
     - `control_profile`
     - workstream wrapper
     - control regime
   - do not preserve old labels like `review_gatekeeper` or `governance_escalation` as active constructs outside historical notes

2. **Align operational guidance with the v2 semantics**
   - keep the A/B/C/D boundary sharp everywhere
   - ensure docs consistently say:
     - Layer C defines regime and wrapper
     - Layer D defines current gate/status
     - `reviewed` does not mean “currently in review”
     - `change_controlled` does not mean “currently awaiting approval”
     - `feature_cell` is not a mode or state

3. **Resolve template/example compatibility**
   - inspect task/workstream templates and filled examples
   - decide whether to:
     - migrate them to v2 Layer C representation now,
     - or keep them as a compatibility layer with explicit explanation
   - do not leave mixed conventions unexplained

4. **Handle the old Layer C v1.1 umbrella doc deliberately**
   - decide whether it should remain as:
     - historical background with a superseded banner and pointer,
     - or a shorter historical stub
   - do not leave it looking like an equally current primary concept doc

5. **Improve agent legibility**
   - keep docs skimmable
   - reduce conceptual drift
   - prefer explicit structure over prose-heavy ambiguity where useful
   - keep ontology small

## Files to inspect carefully

At minimum inspect and align:

- `docs/harness/AGENTS.md`
- `docs/harness/README.md`
- `docs/harness/policies/routing-rules.md`
- `docs/harness/workflows/task-execution-loop.md`
- `docs/harness/workflows/workstream-loop.md`
- `docs/harness/workflows/checkpoint-review-loop.md`
- `docs/harness/templates/task-card.template.md`
- `docs/harness/templates/workstream-card.template.md`
- `docs/harness/examples/example-task-card-filled.md`
- `docs/harness/examples/example-workstream-card-filled.md`
- `docs/harness/prompts/execution-agent.md`
- `docs/harness/prompts/resume-agent.md`

Also inspect adjacent concept docs for stale Layer C teaching:

- `docs/harness/concepts/layer-c-overlays-containers.md`
- `docs/harness/concepts/layer-a-taxonomy.md`
- `docs/harness/concepts/layer-b-operating-modes.md`
- `docs/harness/concepts/layer-d-lifecycle-control-plane.md`

## Specific issues to resolve

### A. Overlay-era language still used as live operational vocabulary

Look for terms like:

- overlay
- overlays
- overlays/container
- review_gatekeeper
- governance_escalation

For each occurrence, decide whether it is:

- stale language that should be rewritten,
- acceptable historical note,
- or explicit compatibility language that needs clarification

### B. Artifact schema mismatch

Current templates and examples may still use old fields such as `overlays: []`.

Make a deliberate choice:

- either migrate the artifact schema to v2 Layer C constructs,
- or keep the old shape temporarily but document clearly how it maps to v2

Do not leave the reader guessing whether those artifacts are canonical or legacy.

### C. Layer C vs Layer D confusion

Remove any wording that could imply:

- reviewed = currently at checkpoint
- change-controlled = always awaiting approval
- feature_cell = status
- feature_cell = mode

### D. Cross-layer teaching drift

Make sure Layer A/B/D docs no longer teach the old Layer C ontology as if it were current.

Keep those edits minimal and boundary-focused.

## Constraints

- Do **not** introduce new Layer C ontology unless clearly necessary.
- Do **not** proliferate presets.
- Do **not** blur Layer C with Layer D.
- Do **not** turn this into a heavyweight PM framework.
- Preserve the v2 decisions already established in `docs/harness/concepts/layer-c/`.

## Deliverables

1. Edit the harness docs directly.
2. Make the alignment concrete, not advisory.
3. At the end, provide a concise summary covering:
   - what you changed
   - what compatibility decisions you made for templates/artifacts
   - whether any semantics changed vs only clarified
   - how you handled the old Layer C v1.1 umbrella doc
   - any remaining follow-up areas

## Validation expectations

Use grep-based verification at minimum for:

- `review_gatekeeper`
- `governance_escalation`
- `overlay`
- `overlays`
- `Layer C overlays/container`
- `checkpoint`
- `awaiting_approval`

Review each remaining occurrence and classify it as:

- acceptable historical note
- acceptable compatibility reference
- stale wording that should have been removed

## Preferred working style

- Be conservative with conceptual changes.
- Be aggressive about consistency fixes.
- If a concept is already good, keep it.
- If full artifact-schema migration is too large for this pass, choose explicit compatibility instead of half-migration.
- Favor durable architecture language over local phrasing accidents.
````

## Compact Context Summary

- The Layer C v2 mini-spec under `docs/harness/concepts/layer-c/` is already aligned.
- Baseline is implicit by default.
- Canonical Layer C constructs are `feature_cell` and `control_profile`.
- Presets are summaries only; normalized fields are authoritative.
- The main harness README now routes to the v2 Layer C directory.
- The remaining work is broader harness alignment, especially AGENTS, workflows, templates, prompts, examples, and adjacent concept docs.
