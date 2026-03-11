# Architecture Doc Rewrite Playbook

## When To Use
Use when rewriting `docs/evergreen/architecture.md` and the goal is to preserve or improve its agent-facing usefulness without changing its role.

This playbook is for maintaining `docs/evergreen/architecture.md` as the durable current-state architecture statement. It is not the routing map for day-to-day code navigation, and it is not a general codebase review guide or product-scope authority.

## Stable Rewrite Inputs
Treat the following as the stable inputs that shape a correct rewrite:

- `docs/evergreen/architecture.md`: target document being rewritten
- `docs/evergreen/agent-routing.md`: paired routing document that owns code-entry and edit guidance
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
- `docs/harness-maintain/context-building-playbook.md`: stable context-building method used before rewrite-specific decisions

## Document Invariants
These invariants must survive any rewrite of `docs/evergreen/architecture.md`:

- It remains a current-state architecture doc, not a future-state design doc.
- It remains architecture-first: it should describe topology, bounded contexts, earned seams, and the gap to MVP.
- It preserves authority separation:
  - `docs/evergreen/mvp.md` owns product scope
  - `docs/evergreen/api-contracts.md` owns stable public API
  - `docs/evergreen/agent-routing.md` owns code-entry routing, implementation maps, edit starting points, and change-impact guidance
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
- It stays local and high-leverage, not a second `AGENTS.md`, not a copy of `docs/delivery/workflow.md`, and not a replacement for `docs/evergreen/agent-routing.md`.

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
- `Topology`
- `Bounded Contexts`
- `Current Architectural Seams`
- `Boundary Between Public API, Internal Architecture, And Planned Work`
- `Gap To MVP`
- `Agent Guardrails`
- `Routing Note`
- `Workflow Alignment`
- `Documentation Authority`

Section intent:

- `Topology`: runtime/storage shape and major deployment boundaries
- `Bounded Contexts`: subsystem-level ownership boundaries
- `Agent Guardrails`: explicit non-inferences and authority boundaries
- `Routing Note`: pointer to `docs/evergreen/agent-routing.md` for operational navigation details

## Rewrite Patterns To Prefer
- Short route blocks with explicit labels such as `Canonical`, `Reference only`, `Execution history`, and `Implemented internal`
- Compact architecture bullets that describe subsystem boundaries and earned seams without file-by-file inventory
- Guardrail bullets that say what must not be inferred from the current code
- Clear pointers to `docs/evergreen/agent-routing.md` whenever the detail starts becoming operational rather than architectural

## Anti-Patterns
Do not let a rewrite do any of the following:

- add future architecture as if already implemented
- collapse internal scaffolding into public API
- copy workflow theory or product framing into `docs/evergreen/architecture.md`
- redefine evaluation semantics locally
- copy the implementation map, edit starting points, or change-impact list out of `docs/evergreen/agent-routing.md`
- claim a seam is real without proof points
- let `implemented internal` drift into `stable` by wording alone

## Acceptance Checks
A rewrite is successful only if the resulting `docs/evergreen/architecture.md` satisfies all of the following:

- A reader can understand the current system shape without reading a file-by-file repo inventory.
- A coding agent can identify the owning architecture doc before changing semantics or scope wording.
- A reader can tell what is public, what is internal, and what is still planned.
- No section competes with `docs/evergreen/mvp.md`, `docs/evergreen/api-contracts.md`, or the evergreen eval docs for semantic ownership.
- Every promoted seam is backed by current code and validation, even if the detailed proving routes live in `docs/evergreen/agent-routing.md`.
- The document remains concise enough to scan quickly.

## Working Rule
- Keep this playbook architecture-doc specific.
- If the rewrite starts turning into a general docs-routing or context-building exercise, stop and move that broader work to `docs/harness-maintain/context-building-playbook.md` or another appropriate harness artifact.
- If a real ownership conflict appears during a rewrite, resolve it by deferring to the owning doc instead of patching the conflict locally inside `docs/evergreen/architecture.md`.
