# API Contracts

**Status:** Verified
**Last verified:** 2026-03-10

## Purpose
This document defines the stable external interfaces that are actually implemented and safe for downstream reliance.

As of 2026-03-10, there are no earned public API contracts in `parity`.

## Current State
The repository does not currently expose a stable user-facing package API, service API, or CLI contract that downstream callers should rely on.

Implementation experiments, internal seams, prototypes, and workstream design material do not count as evergreen API contracts.

## Scope
### In Scope
- explicit statement of whether any stable public contract exists
- the boundary between implemented experiments and promised interfaces

### Out Of Scope
- planned MVP interfaces
- draft ingestion, parsing, retrieval, answer, or citation payloads
- internal module boundaries
- prototype CLIs or dev-only commands
- workstream proposals and delivery drafts

## Stable Interfaces
There are currently no stable public interfaces.

Specifically, this means:

- no stable Python package API is defined
- no stable HTTP or service API is defined
- no stable CLI behavior is defined
- no request or response schema is defined as public contract

## Compatibility And Change Control
Because no public API contract has been earned yet:

- code in `src/parity/` should be treated as internal and changeable
- renames, removals, and signature changes are not contract breaks unless this document is updated first
- future interfaces should only be added here after they are implemented and intentionally supported for downstream use

## Promotion Rule
An interface should appear in this file only when all of the following are true:

- it exists in the codebase
- its behavior is exercised by tests or equivalent validation
- the team intends downstream callers to rely on it
- the team is willing to treat incompatible changes as breaking changes

Until then, the correct evergreen position is that `parity` has no stable API contracts.

## Relationship To Other Docs
- [`docs/evergreen/mvp.md`](./mvp.md) describes the target product, not current API reality.
- [`docs/evergreen/architecture.md`](./architecture.md) describes current repo shape and internal seams, not a promise of stable external interfaces.
- `docs/delivery/` and `docs/workstreams/` may describe future contracts, but they are not current public API commitments.
