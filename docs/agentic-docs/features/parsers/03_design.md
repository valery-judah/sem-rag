# Design: Parsers

## Source of Truth
Detailed parser implementation design currently lives in:
- [docs/parsers/03_design.md](/Users/val/projects/rag/sem-rag/docs/parsers/03_design.md)

## Local Tracking Purpose
This file is the feature-local design entrypoint in the `/docs/features/parsers/` structure.

## Design Scope to Preserve
- deterministic parser data flow
- canonicalization strategy by content type
- heading/tree construction with tie-breakers
- range and anchor derivation policy
- observability events and payload shape
- limitations/deferred items

## Synchronization Rule
If parser design decisions change, update this file and canonical design docs in the same PR until migration completion.
