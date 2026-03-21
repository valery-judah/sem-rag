---
artifact_kind: workstream
id: WS-026
title: Dto Factories
work_type: refactor
status: active
owner:
created: 2026-03-20
updated: 2026-03-20
---

# Summary
Define the ownership model for DTO construction and internal-model conversion at
the app boundary introduced by WS-025.


## Current status
- WS-025 established app services as an earned seam for API-facing orchestration.
- DTO construction responsibility is still not fully settled across services,
  app schemas, and query review models.
- `WS-026-design-options.md` is the Codex-owned decision input for choosing the
  boundary pattern.

## Next step
- Resolve whether WS-026 should use DTO-owned factories by default or adopt a
  hybrid conversion rule.
