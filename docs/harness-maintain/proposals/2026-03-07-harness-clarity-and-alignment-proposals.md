# Harness clarity and alignment proposals

## Context

This note was produced while using the harness to create a real task card for parser-contract work.

The concrete flow was:

1. read `docs/harness/README.md`,
2. follow the intake and task-shaping guidance,
3. choose the appropriate Layer B mode,
4. create a task card in `docs/harness/active/tasks/`,
5. update `docs/harness/indexes/active-tasks.md`.

The goal of this note is to record where the harness felt ambiguous, stale, or internally misaligned during actual use, and to propose targeted follow-up clarifications.

## What was clear enough to operate

Several parts of the harness were clear and usable:

- the top-level harness entry flow was good enough to operate from,
- task-first, workstream-later guidance was clear,
- `contract_builder` was a clear Layer B fit for the parser-contract slice,
- the task card frontmatter model is now mostly coherent across the top-level README, intake loop, and task template.

This note is therefore not a claim that the harness is unusable. It is a record of the places where real operation still required avoidable interpretation.

## Friction observed during real use

### 1. Live vs illustrative artifact ambiguity

`docs/harness/indexes/active-tasks.md` already contained active entries, while `docs/harness/active/tasks/` was empty at the time the new task was created.

That created immediate uncertainty about whether the index was:

- a live operational summary,
- an illustrative example,
- or a placeholder that had never been wired to real task cards.

This matters because the harness positions indexes as lightweight live views, but a user cannot trust that role if the entries do not clearly correspond to real authoritative artifacts.

Related maintainer guidance currently says that empty indexes are acceptable placeholders when the repository is not yet maintaining that view actively. That makes sense for an intentionally unused index, but it weakens operator confidence once an index contains concrete entries.

### 2. Maintainer docs are behind the current Layer C and Layer D canon

`docs/harness-maintain/main.md` still contains compatibility guidance describing task and workstream cards in legacy Layer C shorthand terms such as `container` and `overlays`, even though the active templates and examples were already moved to canonical nested Layer C fields.

The same maintainer file still references `docs/harness/concepts/layer-d-lifecycle-control-plane.md`, even though Layer D now lives under `docs/harness/concepts/layer-d/`.

This creates a specific maintainer problem: the file that is supposed to explain harness evolution policy still reinforces outdated assumptions about what is canonical now versus what is merely historical compatibility context.

### 3. Terminology drift around Layer C

The harness has improved its canonical Layer C language, but not all documents are aligned on the same vocabulary.

Some live docs still talk in terms of `container` and `containers`, while newer surfaces emphasize `feature_cell` and `control_profile`.

The issue is broader than legacy card frontmatter. It affects explanatory language across the harness and maintainer surfaces.

This matters because a reader currently has to infer whether `container` is still a canonical concept term, an acceptable synonym, or a historical label that should only appear in migration context.

### 4. Value normalization is weak at card-authoring time

The harness explains the meaning of Layer A fields well enough to fill a task card, but it does not make the allowed or preferred value sets especially clear during authoring.

This was most noticeable for fields such as:

- `intent`
- `knowledge_locality`
- `dependency_complexity`

The semantics are understandable, but the docs do not make it obvious whether a chosen value is canonical, merely conventional, or ad hoc.

That means real card authoring still depends on local interpretation rather than a light but visible normalization rule.

### 5. Control-profile activation is still somewhat judgment-heavy

The specific ambiguity encountered during task creation was whether a contract-definition task should immediately carry a reviewed-style control profile, or whether it should remain baseline until a true review boundary exists.

The docs correctly emphasize sparse Layer C usage and correctly describe review boundaries conceptually. What is still missing is a short operational decision rule for early contract work:

- draft under baseline control while shaping the contract,
- then add `reviewed` when the slice should pause at a real review boundary before further implementation-aligned progress.

Without that explicit rule, the operator still has to improvise slightly when classifying contract-heavy slices.

## Proposed follow-up decisions

### Proposal A. Make index status explicit

Each index should explicitly declare whether it is:

- a live derivative summary, or
- a placeholder / illustrative view.

If an index contains entries, those entries should correspond to real authoritative artifacts.

A short status line near the top of each index would reduce ambiguity without changing the harness model.

### Proposal B. Update `docs/harness-maintain/` to current canon

`docs/harness-maintain/main.md` should be realigned with current harness canon.

That includes:

- removing or rewriting outdated Layer C shorthand guidance as current practice,
- replacing stale Layer D monolith references with the `docs/harness/concepts/layer-d/` reference set,
- checking `maintain-readme.md` and `maintain-agents.md` for older overlays/containers framing and aligning them with current usage.

The maintainer docs should not lag behind the operator-facing docs on what is canonical now.

### Proposal C. Decide whether `container` remains a live conceptual term

The harness should make an explicit choice:

- either keep `container` as an accepted explanatory term for `feature_cell`,
- or retire it from live docs and keep it only in historical / compatibility notes.

The important thing is not which choice wins. The important thing is that README, playbook, policies, templates, and maintainer docs all use the same choice consistently.

### Proposal D. Add light value-normalization guidance for card authors

The harness should provide lightweight normalization help for commonly authored Layer A values.

This does not require full schema enforcement in the same pass. It can be as small as:

- canonical example values,
- a short registry-style note,
- or direct field guidance in templates and workflows.

The goal is to reduce author improvisation without expanding the taxonomy unnecessarily.

### Proposal E. Clarify when to add a reviewed control profile

The harness should add one short rule in intake and execution guidance:

- baseline while drafting,
- add `reviewed` when progress should pause at a real review boundary before implementation or downstream continuation.

This keeps Layer C sparse while making review-control activation more predictable.

## Reasoning behind the proposals

These proposals come from real harness usage rather than abstract cleanup. The friction appeared while trying to create and index a real task card, not while reading the docs passively.

The main concern is operator confidence. A harness should make it obvious:

- which docs are authoritative,
- which terms are current,
- which derivative artifacts can be trusted,
- and when control context should be activated.

None of these proposals require expanding the harness model. They are mainly about reducing stale wording, clarifying live-vs-historical status, and lowering interpretation load for routine operation.

## Suggested implementation order

1. Update `docs/harness-maintain/main.md` so maintainer policy stops reinforcing outdated assumptions.
2. Align maintainer docs and top-level live docs on Layer C terminology.
3. Tighten index-status guidance so derivative artifacts are easier to trust.
4. Add lightweight normalization and control-profile clarification for card authors.

## Expected outcome

After these changes, a maintainer or agent should be able to create a real task card without needing to infer:

- whether indexes are trustworthy,
- whether legacy Layer C card shorthand is still canonical,
- whether `container` is current terminology or historical language,
- or when a reviewed control profile should be activated.
