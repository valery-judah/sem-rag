from __future__ import annotations

import pytest

from parity.query import AnswerMode, DuplicateSuppressionMode, QueryPolicyDefaults, SupportState
from parity.query.contracts import QueryPolicyOverride
from parity.query.policies import apply_policy_overrides

pytestmark = pytest.mark.contract


def test_query_policy_defaults_are_explicit() -> None:
    policy = QueryPolicyDefaults.build()

    assert policy.retrieval_candidate_cap == 24
    assert policy.evidence_set_cap == 8
    assert policy.neighbor_expansion_enabled is True
    assert policy.neighbor_expansion_cap == 1
    assert policy.duplicate_suppression_mode is DuplicateSuppressionMode.HEADING_AND_LOCATOR
    assert policy.context_token_budget == 4000
    assert policy.deterministic_tie_break_order == (
        "score_desc",
        "doc_id_asc",
        "chunk_id_asc",
    )
    assert policy.support_assessment_policy_version == "support_assessment.deterministic.v1"
    assert policy.answer_mode_policy_version == "answer_mode_policy.deterministic.v1"
    assert policy.source_navigation_requires_locator is True
    assert policy.conflict_caps_support_at_partial is True
    assert policy.provenance_weakness_caps_support_at_partial is True


def test_query_policy_defaults_cover_every_support_state() -> None:
    policy = QueryPolicyDefaults.build()

    assert policy.answer_mode_by_support_state == {
        SupportState.SUFFICIENT: AnswerMode.DIRECT_ANSWER,
        SupportState.PARTIAL: AnswerMode.QUALIFIED_ANSWER,
        SupportState.INSUFFICIENT: AnswerMode.FULL_ABSTENTION,
    }


def test_query_policy_overrides_merge_cleanly() -> None:
    base = QueryPolicyDefaults.build()

    overridden = apply_policy_overrides(
        base,
        QueryPolicyOverride(
            retrieval_candidate_cap=12,
            neighbor_expansion_enabled=False,
            context_token_budget=2500,
        ),
    )

    assert overridden.retrieval_candidate_cap == 12
    assert overridden.neighbor_expansion_enabled is False
    assert overridden.context_token_budget == 2500
    assert overridden.evidence_set_cap == base.evidence_set_cap
