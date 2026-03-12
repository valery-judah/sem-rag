# Context-Building Playbook

## When To Use
Use when you need a stable method for building context before changing code or docs.

This playbook is for agent and engineer navigation: what to read first, how to separate authority from execution history, how to distinguish implemented truth from inference, and how to confirm a seam is real.

It is not a product-scope doc, a current-state architecture doc, or a workstream stage note.

## Stable Inputs
Treat the following as the stable inputs for context building:

- `docs/evergreen/mvp.md`
- `docs/evergreen/architecture.md`
- `docs/evergreen/agent-routing.md`
- `docs/evergreen/api-contracts.md`
- `docs/README.md`
- `AGENTS.md`

Use workstream plans, stage notes, code seams, and tests after those stable inputs.

## Core Route
Use this default order unless a task has a clear reason to do otherwise:

1. Open the canonical scope and current-state docs first.
2. Open the relevant staged plan and latest implemented stage note second.
3. Open the owning code seams third.
4. Open the proving tests fourth.

Use that sequence to answer four different questions:

- evergreen docs answer what is canonical, what is internal-only, and what is still missing
- staged plans and stage notes answer what the subsystem is trying to become and what the current phase actually earned
- code seams answer where the behavior is implemented today
- tests answer whether a seam is implemented repo truth or still just design framing

## Decision Rules

Keep two categories separate while building context:

- supported by current repo truth:
  - backed by implemented code and proving tests
- inference due to missing seam:
  - required interpretation because the repo does not yet have a stronger primitive such as a workspace registry, ACL layer, shared inference adapter, or public API contract

Do not treat workstream docs as canonical truth when evergreen docs or exercised code disagree.

Do not treat implemented internal seams as stable public interfaces unless `docs/evergreen/api-contracts.md` says so.

## Query Context Route
For query subsystem work, use this stable route before adding phase-specific discovery:

1. `docs/evergreen/mvp.md`
2. `docs/evergreen/architecture.md`
3. `docs/evergreen/agent-routing.md`
4. `docs/evergreen/api-contracts.md`
5. `docs/workstreams/WS-006-query-lifecycle/query_subsystem_staged_implementation_plan.md`
6. `docs/workstreams/WS-006-query-lifecycle/07_design.md`
7. the latest implemented WS-006 stage note
8. `src/doc_forge/query/service.py`, `src/doc_forge/query/contracts.py`, `src/doc_forge/query/persistence.py`, and `src/doc_forge/query/stages/`
9. `src/doc_forge/readmodels/documents.py`
10. `src/doc_forge/app/api.py` and `src/doc_forge/app/deps.py`
11. `tests/readmodels/test_queryable_corpus_read_model.py`, `tests/query/`, and `tests/app/test_runtime_api.py`

The current workstream stage note should then add only the phase-specific route changes on top of this baseline.

## Outputs
A good context-building pass should leave the reader able to state:

- the goal and scope boundary
- the owning canonical doc
- the owning code seams
- the proving tests
- which decisions are supported by current repo truth
- which decisions are still inference because the stronger seam does not exist yet

## Working Rule
- Keep this playbook stable and reusable.
- Do not fill it with phase-specific routes that belong in workstream stage notes.
- If a rule is about rewriting `docs/evergreen/architecture.md` specifically, keep it in `docs/harness-maintain/architecture-doc-rewrite.md` instead.
