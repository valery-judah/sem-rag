# Harness Agent Guide

## Purpose
This file gives short practical guidance for humans and agents using the docs harness.

Use it together with the repo root `AGENTS.md`:
- root `AGENTS.md` remains authoritative for repo-wide command rules, validation defaults, and hard constraints
- this file explains how to start a new feature workstream and how to treat the generated workstream card

## Starting A New Feature Workstream
If the task is to start a new non-trivial feature, run:

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
- Use the script to create the workstream card.
- Treat the generated card as the canonical artifact for the workstream.
- Fill the placeholders progressively as the work becomes clearer.
- Add `decisions.md`, `evidence.md`, `handoff.md`, or `notes.md` only when they help continuity or validation.

## Command Rule
- Use root `AGENTS.md` for repo-wide command conventions and validation defaults.
- If `workstream.md` later includes useful commands, treat them as local notes, not as a separate command authority.
