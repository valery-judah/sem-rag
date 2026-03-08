# Docs Harness

## Purpose
`docs/harness/` holds reusable documentation scaffolding for this repository: taxonomy, templates, conventions, playbooks, and helper scripts for humans and agents.
It supports the canonical docs layout rooted at `docs/evergreen/`, `docs/workstreams/`, `docs/adrs/`, and `docs/harness/`.

## When To Use
- Starting a new workstream
- Creating durable or time-scoped docs in a consistent shape
- Checking repo documentation conventions before adding new material

## Layout
- `taxonomy/`: naming and lifecycle vocabulary for workstreams
- `templates/`: starter files for workstreams, evidence, handoff, decisions, and ADRs
- `conventions/`: lightweight rules for frontmatter, context loading, and ADR placement
- `playbooks/`: short procedures by work type
- `scripts/`: simple shell helpers for initializing and listing docs areas

## Placement Rules
- Durable system truth belongs in `docs/evergreen/`.
- Time-scoped execution history belongs in `docs/workstreams/`.
- Durable architectural decisions belong in `docs/adrs/`.
- RFC-like proposal material belongs inside the relevant workstream, not in a global `docs/rfcs/` directory.

## Starter Workflow
1. Read the relevant evergreen docs.
2. For a new feature workstream, run `docs/harness/scripts/new-feature-workstream.sh <slug>`.
3. Treat `docs/workstreams/WS-###-<slug>/workstream.md` as the canonical entrypoint artifact.
4. Add decisions, evidence, handoff, and notes artifacts only when they improve continuity or validation.
5. Elevate cross-cutting durable decisions to ADRs when needed.
