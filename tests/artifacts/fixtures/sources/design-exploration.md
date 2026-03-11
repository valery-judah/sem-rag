# Document Lifecycle Architecture for MVP

## Purpose

Define the implementation design for the MVP document lifecycle as an internal HTTP service with background workers.

This copied fixture is based on the workstream design exploration and keeps only the sections needed for stable artifact regression tests.

## Scope alignment

This design is constrained by the current MVP framing and lifecycle requirements.

### Inputs

Supported source types:

* text-based PDF
* Markdown

Unsupported inputs must fail explicitly:

* scanned PDFs requiring OCR
* image-centric documents
