# WS-001 Organization Note

This file remains as a non-canonical lead note. The authoritative WS-001 artifacts are:

- `workstream.md` for execution tracking
- `contract-lock.md` for the locked Phase 1 contract
- `seam.md` for the seam definition
- `status.md` for current decisions and deferrals
- `handoff.md` for downstream assumptions

## Intent

WS-001 exists to unblock Phase 2 and Phase 3 by locking only the globally load-bearing interface layer: shared schemas, answer and citation shape, lifecycle semantics, provenance guarantees, and domain boundaries.

## Guardrails

- Keep contract lock narrow and internal.
- Prefer executable validation over prose-only agreement.
- Classify unresolved issues as `locked now`, `deferred within MVP`, or `deferred beyond MVP`.
- Do not let local heuristics become hidden global requirements.

## Current Practical Artifact Set

- workstream execution tracker
- canonical contract artifact
- contract seam note
- internal schema package
- contract validation tests
- seam validation tests
- status tracker
- handoff note
