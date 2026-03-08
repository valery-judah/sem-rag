# Context Loading

## Purpose
This file describes the order an agent or human should use when loading context for a task.

## When To Use
Follow this procedure before starting a change, review, or handoff.

## Load Order
1. Read the relevant docs in `docs/evergreen/`.
2. Open the active workstream folder in `docs/workstreams/`, if one exists.
3. Read related ADRs in `docs/adrs/` for durable decisions.
4. Check recent evidence and handoff notes before making changes.

## Working Rule
- Load only the docs needed for the current task.
- Prefer durable docs first, then active execution history.
- If a decision is still local and time-scoped, keep it in the workstream until it needs ADR status.
