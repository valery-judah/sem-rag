# Phase 2 Framing

## Objective
Turn RFC Phase 2 into the first reviewable seed-corpus package for the eval harness: a mixed-format corpus manifest, scenario catalog, baseline dataset v1, annotation guide, and review log that apply the locked evaluation semantics and are stable enough for end-to-end prototype comparison.

## Input Map

### Docs And Artifacts That Influence Decisions

#### Product Scope And Boundary
- `docs/evergreen/mvp.md`
- `docs/evergreen/architecture.md`
- `docs/evergreen/api-contracts.md`

#### Canonical Evaluation Semantics
- `docs/delivery/eval-vocabulary.md`
- `docs/delivery/eval-support-semantics.md`
- `docs/delivery/eval-scenario-taxonomy.md`
- `docs/delivery/eval-failure-taxonomy.md`

#### Delivery Rationale And Phase Definition
- `docs/delivery/workflow.md`
- `docs/delivery/eval-harness-rfc-sections-1-10.md`
- `docs/delivery/eval-harness-rfc-sections-11-15.md`

#### Existing Workstream Artifacts
- `docs/workstreams/WS-003-seed-corpus/workstream.md`
- `docs/workstreams/WS-001-eval-harness/eval-harness.md`
- `docs/workstreams/WS-002-semantic-lock/eval-vocabulary-extracted-baseline.md`
- `docs/workstreams/WS-002-semantic-lock/eval-scenario-taxonomy-extracted-baseline.md`

#### Current Implementation And Validation Artifacts
- `src/doc_forge/evaluation/`
- `src/doc_forge/_contracts/`
- `tests/test_evaluation_harness.py`
- `tests/test_contracts.py`
- `tests/test_contract_seam.py`

## Primary Outputs

### Corpus Manifest

### Scenario Catalog

### Baseline Dataset v1

### Annotation Guide

### Review Log

## Key Activities

### Choose Representative Mixed-Format Documents

### Author Initial Cases Across All Required Scenario Classes

### Peer Review Annotations

### Create Smoke, Full, And Release Suite Definitions

## Exit Criteria

### Baseline v1 Exists And Is Reviewable End-To-End

### Mixed-Format Coverage Is Present

### Insufficient-Evidence Cases Are Represented

### The Dataset Is Stable Enough For Prototype Comparison
