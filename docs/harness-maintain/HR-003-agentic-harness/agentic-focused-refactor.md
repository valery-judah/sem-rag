# Agentic-Focused Refactor

## Purpose
This note is a non-canonical technical reflection written to support later `agentic-harness` design work.

It captures:
- the reasoning behind the recent semantic-lock work in `docs/workstreams/WS-002-semantic-lock/workstream.md`
- the methods used to tighten semantic authority and agent-facing docs routing
- the principles that appear reusable for future `agentic-harness` implementation work

This note interprets prior changes. It does not override `docs/evergreen/` authority or redefine MVP scope.

## Change Surface Reviewed
The reflection is grounded in the following recent changes:

- `docs/workstreams/WS-002-semantic-lock/workstream.md`: semantic-lock framing, review, and closure
- `docs/delivery/eval-vocabulary.md`: glossary and layer-name authority
- `docs/delivery/eval-support-semantics.md`: support-state, citation, and abstention authority
- `docs/delivery/eval-scenario-taxonomy.md`: frozen scenario-class authority for baseline authoring
- `docs/delivery/eval-failure-taxonomy.md`: failure-class authority
- `docs/delivery/workflow.md`: workflow cleanup to remove competing semantic authority
- `docs/delivery/eval-harness-rfc-sections-1-10.md`: normative harness guidance aligned to evergreen semantics
- `docs/delivery/eval-harness-rfc-sections-11-15.md`: operating-model guidance aligned to evergreen semantics
- `AGENTS.md`: top-level agent routes
- `docs/README.md`: task-first docs index
- `docs/evergreen/architecture.md`: local `Read Next` routes
- `docs/evergreen/mvp.md`: local `Read Next` routes

## Reasoning
### Why semantic authority had to be centralized first
`agentic-harness` work will eventually rely on scenario classes, support-state labels, failure classes, and citation expectations as executable concepts. If those meanings drift across evergreen docs, RFCs, workflow notes, and workstreams, any agent-driven harness logic will encode unstable semantics and produce noisy or non-comparable results.

The semantic-lock work therefore established a prerequisite: define one owning document for each semantic area and make downstream docs inherit that authority instead of competing with it.

### Why agent-facing routing mattered
The repo already had the right documents, but not always the fastest agent-facing discovery path. A coding agent benefits less from long explanatory prose than from:

- clear authority cues
- standalone file paths that are easy to open or copy
- short task-first route blocks
- predictable local follow-up links in the highest-leverage entry docs

That routing refactor was not just cosmetic. It reduced discovery cost and made later agentic workflows more likely to start from the correct authority doc.

### Why internal tooling should separate truth from history
The recent work reinforced a useful split:

- `docs/evergreen/`: canonical truth
- `docs/delivery/`: rationale and implementation-facing guidance
- `docs/workstreams/`: time-scoped execution history and local reflection

For `agentic-harness`, this separation matters because internal tooling work will generate many local decisions and experiments. Without a clear distinction, agents and humans will both overfit to historical notes or drafts instead of the current source of truth.

## Methods
### 1. Identify drift and duplicate authority
The first method was comparative review across evergreen docs, RFC sections, workflow guidance, and workstream records. The useful question was not only "is this statement wrong?" but also "does this doc appear to own semantics it should merely reference?"

### 2. Tighten ownership boundaries
The cleanup treated semantic ownership as an architectural boundary:

- vocabulary and layer names stay in `docs/delivery/eval-vocabulary.md`
- support-state, citation, and abstention rules stay in `docs/delivery/eval-support-semantics.md`
- scenario classes stay in `docs/delivery/eval-scenario-taxonomy.md`
- failure classes stay in `docs/delivery/eval-failure-taxonomy.md`

Other docs can apply these concepts, but they should not redefine them locally.

### 3. Normalize instead of inventing
Where wording drift existed, the refactor preferred normalization over expansion. For example, support-state language was tightened to the locked labels:

- `sufficient support`
- `partial support`
- `insufficient support`

This avoids creating parallel vocabularies that appear equivalent until they diverge operationally.

### 4. Optimize routes around agent behavior
The routing refactor assumed an agent wants to answer:

1. which doc is authoritative here?
2. what should I open next?

That led to:

- task-first route blocks
- standalone repo-relative paths
- explicit labels such as `Canonical`, `Reference only`, and `Execution history`
- short local `Read Next` blocks only in high-leverage entry docs

## What Changed
### Semantic changes
- Evergreen evaluation docs became the explicit semantic source of truth.
- Workflow and RFC wording were pruned or normalized so they no longer acted as competing semantic authorities.
- Scenario-class naming was frozen for baseline authoring and reused consistently downstream.
- Failure-taxonomy usage was aligned so `answering failure`, `citation failure`, and `failure-quality failure` remain distinct.

### Routing changes
- `AGENTS.md` became a stronger top-level task router for coding agents.
- `docs/README.md` gained task-first quick routes and an evaluation-docs map in the same style.
- `docs/evergreen/architecture.md` and `docs/evergreen/mvp.md` gained local `Read Next` blocks.
- Standalone repo-relative paths were preferred over prose-heavy references for faster agent discovery.

### Workstream and process changes
- `WS-002` captured semantic lock as completed work rather than leaving semantics half-owned by multiple docs.
- `HR-003` now captures internal `agentic-harness` work on its own maintenance track instead of treating it as an implied continuation of doc_forge runtime history.
- Reflection itself is being treated as a reusable artifact, not just a chat byproduct.

## Principles Extracted
### Canonical semantics must be settled before agent orchestration is useful
Agentic tooling amplifies whatever semantics it consumes. If support states, scenario classes, or failure labels are unstable, orchestration only makes the instability execute faster.

### Agents need authority cues, not just links
A link without a role label forces the reader to infer whether the target is canonical, reference-only, or historical. Agents benefit from that decision being precomputed in the document itself.

### Path visibility beats prose-heavy reference patterns
Short route blocks with standalone repo-relative paths are easier for agents to scan, copy, and open than paragraphs that mention documents indirectly.

### Local mini-maps are only valuable at high-leverage entry docs
Global routing belongs in `AGENTS.md` and `docs/README.md`. Local `Read Next` blocks help only in a few key entry docs. If added everywhere, they become noisy and drift-prone.

### Internal harness work should inherit semantics, not relitigate them
`agentic-harness` should consume locked semantics from evergreen docs. If implementation pressure reveals a real semantic problem, that should be surfaced explicitly rather than quietly patched in local tooling docs.

### Reflection artifacts should capture heuristics, not just outcomes
The high-value part of the recent work was not only the final wording. It was the method: compare authority surfaces, tighten ownership, normalize language, and optimize routing around agent behavior. Capturing those heuristics makes later work more repeatable.

## Implications For Future `agentic-harness` Work
### First implementations should consume frozen semantics
Early harness slices should read scenario classes, support states, and failure classes as stable inputs from evergreen docs rather than embedding local variants.

### Agent workflows should be designed around clear authority and predictable handoff artifacts
If an agent must decide between evergreen, RFC, workflow, and workstream materials without strong routing or authority cues, its planning and implementation quality will be inconsistent.

### Early slices should stay narrow and inspectable
The recent refactor work suggests a practical bias for `agentic-harness`: start with a narrow internal tool boundary that is easy to inspect and compare, rather than broad orchestration across many loosely defined responsibilities.

## Limits And Open Questions
This note reflects documentation and framing work, not runtime harness implementation evidence.

Open questions that later `agentic-harness` work should validate in code:
- Which of these routing and authority principles remain most important once runtime harness components exist?
- What is the first internal deliverable that gains the most leverage from agentic behavior: dataset authoring support, harness skeleton execution, or a narrower orchestration layer?
- Which handoff artifacts should become standard once agentic-harness implementation starts in earnest?

## Practical Use
Use this note when framing future `agentic-harness` work, especially if the next step involves:

- deciding ownership boundaries
- choosing where semantics should live versus where implementation guidance should live
- designing agent-facing docs or handoff paths
- evaluating whether a proposed local note should become evergreen, remain delivery guidance, or stay inside a workstream

Start agentic-harness tasks from `docs/harness-maintain/README.md` so the work is framed on the `HR` track rather than as doc_forge runtime history.

When this note conflicts with current semantic definitions or MVP scope, the canonical docs win:

- `docs/evergreen/mvp.md`
- `docs/delivery/eval-vocabulary.md`
- `docs/delivery/eval-support-semantics.md`
- `docs/delivery/eval-scenario-taxonomy.md`
- `docs/delivery/eval-failure-taxonomy.md`
