# Architecture Doc Rewrite Playbook

## When To Use
Use when rewriting `docs/evergreen/architecture.md` and the goal is to preserve or improve its agent-facing usefulness without changing its role.

This playbook is for maintaining the document as an agent-oriented current-state architecture map. It is not a general codebase review guide and it is not a workflow or product-scope authority.

## Stable Rewrite Inputs
Treat the following as the stable inputs that shape a correct rewrite:

- `docs/evergreen/architecture.md`: target document being rewritten
- `docs/evergreen/mvp.md`: product scope authority
- `docs/evergreen/api-contracts.md`: stable public API authority
- `docs/evergreen/runbook.md`: command and validation authority
- `docs/evergreen/eval-vocabulary.md`: evaluation vocabulary authority
- `docs/evergreen/eval-support-semantics.md`: support-state, citation, and abstention authority
- `docs/evergreen/eval-scenario-taxonomy.md`: scenario-class authority
- `docs/evergreen/eval-failure-taxonomy.md`: failure-class authority
- `docs/delivery/workflow.md`: reference-only rationale for architecture promotion and invariants
- `AGENTS.md`: top-level agent routing and repo rules
- `docs/README.md`: docs system map and authority split

## Document Invariants
These invariants must survive any rewrite of `docs/evergreen/architecture.md`:

- It remains a current-state architecture doc, not a future-state design doc.
- It remains agent-useful first: it should quickly answer `what owns this behavior?` and `what should I open next?`.
- It preserves authority separation:
  - `docs/evergreen/mvp.md` owns product scope
  - `docs/evergreen/api-contracts.md` owns stable public API
  - evergreen eval docs own evaluation semantics
  - `docs/delivery/workflow.md` is reference-only rationale
  - `docs/workstreams/` is execution history
- It clearly distinguishes:
  - stable public API
  - implemented internal architecture
  - planned but not implemented runtime or product capabilities
- It does not imply that fixtures, internal models, or persistence helpers equal an end-to-end product runtime.
- It only promotes seams that are implemented and exercised, not merely proposed, discussed, or recently added to docs.
- It keeps explicit guardrails against overstatement and authority drift.
- It stays local and high-leverage, not a second `AGENTS.md` and not a copy of `docs/delivery/workflow.md`.

## Rewrite Principles
- Truth over elegance: prefer awkward accuracy over smooth overstatement.
- Paths over prose: standalone repo-relative paths are easier for agents to scan and open.
- Routing over exposition: prioritize what an agent should inspect or consult next.
- Normalize, do not reinvent: if another doc owns terminology, reuse that language exactly.
- Proof-backed seams only: if a seam is named as real, point to code and validating tests or fixtures.
- Boundary clarity is part of architecture: document ownership boundaries matter as much as code boundaries.
- Minimal but sufficient context: include enough explanation to prevent wrong edits, but no long theory detours.
- Rewrite for scan speed: headings and bullets should optimize for rapid agent consumption.

## Required Structure For `architecture.md`
Keep this section skeleton unless there is a strong reason to change it:

- `Purpose`
- `When To Use`
- `Agent Routes`
- `Implementation Map`
- `Edit Starting Points`
- `Validated By`
- `Current Architectural Seams`
- `Boundary Between Public API, Internal Architecture, And Planned Work`
- `Agent Guardrails`
- `Change Impact`
- `Workflow Alignment`
- `Documentation Authority`

Section intent:

- `Agent Routes`: authority and navigation
- `Implementation Map`: what exists, where it lives, when to open it
- `Validated By`: proof that a seam is real
- `Agent Guardrails`: explicit non-inferences and authority boundaries
- `Change Impact`: likely follow-on files or docs to inspect after an edit

## Rewrite Patterns To Prefer
- Short route blocks with explicit labels such as `Canonical`, `Reference only`, `Execution history`, and `Implemented internal`
- Compact implementation bullets that pair each module or path with the task it owns
- Edit entry sections that start from likely coding tasks rather than file inventory alone
- Validation references that show which tests or fixtures exercise a claimed seam
- Guardrail bullets that say what must not be inferred from the current code
- Change-impact notes that warn about likely downstream docs or tests to revisit

## Anti-Patterns
Do not let a rewrite do any of the following:

- add future architecture as if already implemented
- collapse internal scaffolding into public API
- copy workflow theory or product framing into `docs/evergreen/architecture.md`
- redefine evaluation semantics locally
- remove authority labels from route sections
- replace path-first bullets with prose-heavy narrative
- list modules without saying when an agent should open them
- claim a seam is real without proof points
- let `implemented internal` drift into `stable` by wording alone

## Acceptance Checks
A rewrite is successful only if the resulting `docs/evergreen/architecture.md` satisfies all of the following:

- A coding agent can identify the owning file for a change without a repo-wide search.
- A coding agent can identify the owning doc before changing semantics or scope wording.
- A reader can tell what is public, what is internal, and what is still planned.
- No section competes with `docs/evergreen/mvp.md`, `docs/evergreen/api-contracts.md`, or the evergreen eval docs for semantic ownership.
- Every promoted seam is backed by current code and at least one validation surface.
- The document remains concise enough to scan quickly.

## Working Rule
- Keep this playbook architecture-doc specific.
- If the rewrite starts turning into a general docs-routing or workflow-policy exercise, stop and move that broader work to the appropriate harness, workstream, or evergreen artifact.
- If a real ownership conflict appears during a rewrite, resolve it by deferring to the owning doc instead of patching the conflict locally inside `docs/evergreen/architecture.md`.
