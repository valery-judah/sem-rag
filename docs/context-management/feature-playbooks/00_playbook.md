# Agentic Feature Playbook

This page is the routing entrypoint for the feature-playbook system.

## Canonical Playbook

Use [`feature-refactoring/merged_feature_workflow_playbook_v3.md`](./feature-refactoring/merged_feature_workflow_playbook_v3.md) as the canonical playbook for:
- track selection
- artifact ownership
- authority by concern
- entrypoint contract
- conflict-resolution and drift handling
- orchestration procedures
- state transitions
- handoff and completion rules

## Supporting Surfaces

The canonical playbook is implemented through these repo surfaces:
- templates in [`templates/`](./templates/)
- artifact authority in [`../01_artifact_contracts.md`](../01_artifact_contracts.md)
- agent execution rules in [`../03_agent_protocol.md`](../03_agent_protocol.md)

## Usage

For new feature work:
1. Start here.
2. Read the canonical playbook.
3. Create the feature folder from the current templates.
4. Follow the artifact and entrypoint procedures defined in the canonical playbook.

If this routing doc and the canonical playbook ever diverge, the canonical playbook wins.
