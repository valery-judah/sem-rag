# Agent Routing Doc Rewrite Playbook

## When To Use
Use when rewriting `docs/evergreen/agent-routing.md` and the goal is to preserve or improve its usefulness as the repo-navigation map for coding agents.

This playbook is for the operational routing document, not the canonical architecture statement.

## Stable Rewrite Inputs
- `docs/evergreen/agent-routing.md`: target document being rewritten
- `docs/evergreen/architecture.md`: paired architecture document that owns durable system shape
- `docs/evergreen/mvp.md`: product scope authority
- `docs/evergreen/api-contracts.md`: stable public API authority
- `docs/evergreen/runbook.md`: command and validation authority
- evergreen eval docs: semantic authorities
- `docs/README.md`: docs system map and authority split
- `docs/harness-maintain/context-building-playbook.md`: stable context-building method

## Document Invariants
- It remains the coding-agent routing map, not the canonical architecture statement.
- It should quickly answer `what file should I open next?` and `what tests prove this seam?`.
- It should preserve authority labels and doc-ownership routing.
- It may name implementation seams and proving tests in detail.
- It must not imply that implemented internal seams are stable public APIs.
- It should stay task-oriented and scan-friendly.

## Required Structure For `agent-routing.md`
- `Purpose`
- `When To Use`
- `Agent Routes`
- `Implementation Map`
- `Edit Starting Points`
- `Validation Routes`
- `Change Impact`
- `Guardrails`

## Rewrite Principles
- Paths over prose
- Routing over exposition
- Task-oriented entry points over module dumps
- Proof-backed routes only
- Keep durable architecture statements in `docs/evergreen/architecture.md`

## Anti-Patterns
- turning `agent-routing.md` into a second architecture doc
- copying product-scope or evaluation-semantics ownership into local prose
- listing files without saying when to open them
- promoting internal routes or exports into stable API by wording alone

## Working Rule
- If the content becomes about topology, bounded contexts, or gap-to-MVP framing, move it back to `docs/evergreen/architecture.md`.
- If the content becomes a general context-building rule rather than an `agent-routing.md` rewrite rule, move it to `docs/harness-maintain/context-building-playbook.md`.
