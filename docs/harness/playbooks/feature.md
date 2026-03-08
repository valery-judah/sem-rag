# Feature Playbook

## When To Use
Use for new user-visible capability or meaningful product behavior expansion.

## Start Here
- Create the feature workstream with `docs/harness/scripts/new-feature-workstream.sh <slug>`.
- Treat `workstream.md` as the canonical entrypoint for the workstream.
- Add `decisions.md`, `evidence.md`, `handoff.md`, or `notes.md` only when they improve continuity, traceability, or validation.

## Phase 1 Minimum Artifact
- `workstream.md` with the canonical frontmatter and section structure from `docs/harness/templates/workstream.md`
- A single concrete `Next step`
- Initial scope, boundaries, and read-first context captured locally

## Minimum Evidence Expected
- What changed
- Validation performed
- Any compatibility or rollout notes

## Typical Exit Criteria
- Scope is implemented or intentionally narrowed
- Evidence shows the feature was validated
- Evergreen or ADR follow-up is captured when current system truth changed
- Remaining follow-up is captured in handoff or a new workstream
