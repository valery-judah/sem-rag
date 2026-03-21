# WS-026 Design Options: DTO Construction Boundaries

## Purpose
This is the Codex-authored design note for WS-026. It exists to decide how DTO
construction and internal-model conversion should be organized after the
app-layer seam introduced by WS-025.

This note is intentionally separate from `WS-026-roo-analysis.md`.

## Problem Statement
The current app boundary still mixes multiple responsibilities in the same
service layer:

- orchestration of document/query flows
- HTTP and error translation
- DTO construction and conversion

DTO conversion is also inconsistent today:

- some responses are constructed inline field by field
- some responses are produced via `model_validate(..., from_attributes=True)`

That makes the boundary harder to reason about and weakens ownership of the
conversion logic.

## Current Hotspots
The main construction and conversion hotspots are:

- `src/doc_forge/app/services/documents.py`
- `src/doc_forge/app/services/queries.py`
- `src/doc_forge/app/services/internal.py`
- `src/doc_forge/query/review.py`

## Design Goals
- keep app services thin
- preserve the stable HTTP contract
- make boundary ownership explicit
- avoid transport leakage into internal/domain models
- improve discoverability of conversion logic
- keep the solution proportionate to current repo complexity

## Options

### 1. Keep Mapping In Services
Services continue to construct DTOs directly, either explicitly or through
`model_validate(..., from_attributes=True)`.

Pros:

- lowest immediate cost
- no new abstraction
- easy to follow for very small flows

Cons:

- services keep boundary-shaping logic
- mapping stays inconsistent across endpoints
- orchestration and conversion remain coupled
- repeated patterns stay scattered

### 2. DTO-Owned Factories or Classmethods
Target DTOs own their own construction methods, for example:

- `DocumentDetailResponse.from_document(...)`
- `UploadDocumentResponse.from_result(...)`
- `SubmitQueryRequest.to_internal()`
- `QueryAnswerResponse.from_state(...)`

Pros:

- conversion lives with the target contract
- services become thinner and more uniform
- easier to discover mapping rules while editing DTOs
- strong fit for one-source-to-one-target transformations

Cons:

- `app/schemas.py` may become crowded
- DTO modules gain awareness of internal model types
- some methods may still be thin wrappers
- awkward for multi-source or context-heavy assembly

### 3. Dedicated Mapper or Builder Modules
Introduce explicit boundary modules, for example:

- `src/doc_forge/app/mappers/documents.py`
- `src/doc_forge/app/mappers/queries.py`

Pros:

- keeps DTO declarations cleaner
- keeps services thin
- scales better when mapping becomes composed or contextual
- separates boundary logic by context

Cons:

- adds an extra concept and navigation hop
- can become low-value indirection for trivial mappings
- needs naming and ownership discipline

### 4. Source-Model Export Methods
Internal models expose `to_response()` or `to_dto()` behavior directly.

Pros:

- shortest call sites
- conversion lives near the source data

Cons:

- leaks transport concerns into internal models
- weakens dependency direction
- conflicts with the boundary intent of WS-025
- makes app-contract concerns harder to contain

This option should be rejected unless the architecture boundary is deliberately
changed.

### 5. Hybrid Split By Boundary Type
Use DTO-owned factories for simple app-boundary mappings and use dedicated or
local builders where composition is heavier, especially in review/read-model
assembly.

Example split:

- `app/schemas.py` owns simple HTTP-boundary conversions
- `query/review.py` or context-local builders own composed review assembly
- services do not build response payloads inline

Pros:

- matches abstraction size to complexity
- avoids forcing all mappings into one pattern
- keeps simple cases simple
- scales better for query/review composition

Cons:

- needs an explicit style rule
- requires judgment about where the line sits

## Tradeoff Comparison
| Option | Service cleanliness | Boundary purity | Scalability | Discoverability | Complexity overhead |
| --- | --- | --- | --- | --- | --- |
| Keep in services | low | medium | low | medium | low |
| DTO-owned factories | high | medium-high | medium | high | low-medium |
| Dedicated mappers/builders | high | high | high | medium | medium |
| Source-model export methods | high | low | medium | high | low |
| Hybrid split | high | high | high | medium-high | medium |

## Comparison With `WS-026-roo-analysis.md`
The Roo analysis and this note agree on the main diagnosis:

- services currently carry too much DTO-construction logic
- the stable HTTP contract must be preserved
- internal models should not export API DTOs directly

The main difference is scope of the recommendation.

### Where Roo Is Strong
Roo makes a strong case for a simple first rule:

- move conversion responsibility out of services
- put explicit factory methods on DTOs
- keep the app boundary as the adapter layer

That is a good default for the straightforward mappings already visible in:

- `src/doc_forge/app/services/documents.py`
- `src/doc_forge/app/services/internal.py`

In those flows, the source object is usually singular and the target DTO is
clear. Roo's recommendation keeps the change small and reviewable.

### Where Roo Is Too Narrow
Roo treats DTO-owned factories as the primary solution for the whole workstream.
That leaves two issues underexplored:

- `src/doc_forge/query/review.py` already contains composed read-model assembly
  that is more than a simple DTO conversion
- `src/doc_forge/app/schemas.py` may become a mixed contract-plus-builder module
  if every boundary mapping is pushed there indiscriminately

In other words, Roo is strongest on the public app DTO boundary, but weaker on
the internal review/read-model path.

### Where This Note Adds Useful Caution
This note keeps the dedicated-builder and hybrid variants alive because they
better account for:

- mappings that depend on multiple source objects
- read-model assembly that is already context-local to `query/review.py`
- long-term growth pressure on `app/schemas.py`

That does not invalidate Roo's recommendation. It means Roo's recommendation is
better understood as the default for simple cases, not necessarily the universal
rule for every conversion seam.

## Focused Tradeoff Analysis
The real decision is not between five equally likely options. It is between
three serious candidates:

- Roo-style DTO-owned factories everywhere
- dedicated mapper/builder modules
- a hybrid rule

### Roo-style DTO-owned factories everywhere
Best when:

- one source object maps to one DTO
- the mapping is API-boundary specific
- the team wants the smallest immediate refactor

Tradeoffs:

- strongest on simplicity and discoverability
- weaker if query/review assembly keeps growing
- risks overloading `app/schemas.py` with behavior

### Dedicated mapper or builder modules
Best when:

- mappings are composed or contextual
- the team wants a clear adapter layer per bounded context
- DTO declarations should remain mostly shape-only

Tradeoffs:

- strongest on long-term separation and scalability
- weaker on immediacy because it adds another concept
- likely overengineered for today's document/internal endpoint mappings

### Hybrid rule
Best when:

- simple app-boundary mappings can stay local to DTOs
- composed query/review mappings need a different home
- the team wants a policy that scales without forcing premature structure

Tradeoffs:

- strongest on fit-to-shape and architectural durability
- weaker on consistency because it needs explicit style rules
- requires the workstream to define where the line sits

## Synthesis Recommendation
The best synthesis of both notes is:

- adopt Roo's DTO-owned factory approach as the default for simple app-boundary
  conversions
- do not elevate it to a universal rule
- explicitly allow a hybrid escape hatch for composed query/review mappings or
  any conversion that would make `app/schemas.py` carry too much assembly logic

That yields a decision rule instead of a single mechanism:

1. If one internal object cleanly becomes one API DTO, prefer a DTO-owned
   factory/classmethod.
2. If the conversion composes multiple sources, derives summary objects, or is
   already naturally owned by a local read-model module, keep it in a dedicated
   local builder rather than forcing it into `app/schemas.py`.
3. Do not place API-export behavior on internal domain or persistence models.

## Recommendation
Two options are viable:

- prefer DTO-owned factories/classmethods for simple app-boundary mappings
- prefer a hybrid split if query/review composition is expected to grow

Recommendation:

- default to DTO-owned factories at the app boundary for straightforward
  one-object-to-one-DTO mappings
- use a hybrid approach when query/review assembly becomes composed enough that
  it would bloat `app/schemas.py`

Explicit rejection:

- do not put `to_dto()` or `to_response()` methods on internal domain or
  persistence models unless the architectural boundary is intentionally revised

## Decision Questions To Resolve
1. May `app/schemas.py` own adapter behavior, or should it remain declarative?
2. Should query/review assembly stay in `src/doc_forge/query/review.py`, or move
   toward app-boundary builders?
3. Does the repo want one universal conversion rule, or is a hybrid rule
   acceptable?

## Acceptance Checks
- `WS-026-roo-analysis.md` remains separate and untouched in intent
- this note is clearly Codex-authored, not an agent handoff
- the content is decision-oriented rather than implementation-oriented
- no code or API-contract changes are part of this step
