# Frontmatter Conventions

## Purpose
This file defines lightweight frontmatter guidance for markdown docs in this repo.

## When To Use
Use frontmatter when it helps routing, ownership, or status tracking. It is optional unless a local template or workstream explicitly asks for it.

## Suggested Fields
- `title`
- `status`
- `owner`
- `created`
- `updated`
- `tags`

## Minimal Example
```yaml
---
title: Parser Contracts
status: active
owner: platform
created: 2026-03-08
updated: 2026-03-08
tags:
  - parsing
  - contracts
---
```

## Guidance
- Keep fields short and factual.
- Prefer headings in the body for the actual document structure.
- Do not add frontmatter just for uniformity if the document is simple and local.
