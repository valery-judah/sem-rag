# Harness Agent Guide

## Purpose
This file gives short practical guidance for humans and agents using the docs harness.

Use it together with the repo root `AGENTS.md`:
- root `AGENTS.md` remains authoritative for repo-wide command rules, validation defaults, and hard constraints
- this file explains how to use the shared docs harness and its standard workstream scaffold

## Starting A Workstream
If the task is to start a new non-trivial workstream, first use `docs/harness/taxonomy/workstream-taxonomy.md` to choose the right `work_type`.

Then run:

```bash
docs/harness/scripts/new-feature-workstream.sh <slug>
```

Example:

```bash
docs/harness/scripts/new-feature-workstream.sh parser-contract-cleanup
```

This creates:

```text
docs/workstreams/WS-###-<slug>/workstream.md
```

## What The Generated `workstream.md` Is
The generated `workstream.md` is an initial workstream card, not a fully framed plan.

At creation time it is valid for the file to contain placeholders for:
- objective details
- relevant context
- boundaries
- commands
- validation notes

Those details can be filled later during framing and execution.

## Working Rule
- Use root `AGENTS.md` for repo-level routing decisions before creating a workstream card.
- Use `docs/harness/taxonomy/workstream-taxonomy.md` when classifying the workstream and choosing a matching playbook.
- Treat the generated card as the canonical artifact for the workstream.
- Fill the placeholders progressively as the work becomes clearer.
- Add `decisions.md`, `evidence.md`, `handoff.md`, or `notes.md` only when they help continuity or validation.

## Command Rule
- Use root `AGENTS.md` for repo-wide command conventions and validation defaults.
- If `workstream.md` later includes useful commands, treat them as local notes, not as a separate command authority.
