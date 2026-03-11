"""Canonical query policy defaults and runtime policy objects."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .contracts import AnswerMode, DuplicateSuppressionMode, QueryPolicyOverride, SupportState


class QueryPolicy(BaseModel):
    """Validated runtime policy used by query orchestration."""

    model_config = ConfigDict(extra="forbid")

    retrieval_candidate_cap: int = Field(ge=1)
    evidence_set_cap: int = Field(ge=1)
    neighbor_expansion_enabled: bool
    neighbor_expansion_cap: int = Field(ge=0)
    duplicate_suppression_mode: DuplicateSuppressionMode
    context_token_budget: int = Field(ge=1)
    deterministic_tie_break_order: tuple[str, ...] = Field(min_length=1)
    answer_mode_by_support_state: dict[SupportState, AnswerMode]
    support_assessment_policy_version: str = Field(min_length=1)
    answer_mode_policy_version: str = Field(min_length=1)
    source_navigation_requires_locator: bool
    conflict_caps_support_at_partial: bool
    provenance_weakness_caps_support_at_partial: bool
    citation_include_heading_path: bool
    citation_include_locator: bool


class QueryPolicyDefaults:
    """Canonical source of default query policy values."""

    RETRIEVAL_CANDIDATE_CAP = 24
    EVIDENCE_SET_CAP = 8
    NEIGHBOR_EXPANSION_ENABLED = True
    NEIGHBOR_EXPANSION_CAP = 1
    DUPLICATE_SUPPRESSION_MODE = DuplicateSuppressionMode.HEADING_AND_LOCATOR
    CONTEXT_TOKEN_BUDGET = 4000
    DETERMINISTIC_TIE_BREAK_ORDER = ("score_desc", "doc_id_asc", "chunk_id_asc")
    ANSWER_MODE_BY_SUPPORT_STATE = {
        SupportState.SUFFICIENT: AnswerMode.DIRECT_ANSWER,
        SupportState.PARTIAL: AnswerMode.QUALIFIED_ANSWER,
        SupportState.INSUFFICIENT: AnswerMode.FULL_ABSTENTION,
    }
    SUPPORT_ASSESSMENT_POLICY_VERSION = "support_assessment.deterministic.v1"
    ANSWER_MODE_POLICY_VERSION = "answer_mode_policy.deterministic.v1"
    SOURCE_NAVIGATION_REQUIRES_LOCATOR = True
    CONFLICT_CAPS_SUPPORT_AT_PARTIAL = True
    PROVENANCE_WEAKNESS_CAPS_SUPPORT_AT_PARTIAL = True
    CITATION_INCLUDE_HEADING_PATH = True
    CITATION_INCLUDE_LOCATOR = True

    @classmethod
    def build(cls) -> QueryPolicy:
        """Return the canonical default policy object."""

        return QueryPolicy(
            retrieval_candidate_cap=cls.RETRIEVAL_CANDIDATE_CAP,
            evidence_set_cap=cls.EVIDENCE_SET_CAP,
            neighbor_expansion_enabled=cls.NEIGHBOR_EXPANSION_ENABLED,
            neighbor_expansion_cap=cls.NEIGHBOR_EXPANSION_CAP,
            duplicate_suppression_mode=cls.DUPLICATE_SUPPRESSION_MODE,
            context_token_budget=cls.CONTEXT_TOKEN_BUDGET,
            deterministic_tie_break_order=cls.DETERMINISTIC_TIE_BREAK_ORDER,
            answer_mode_by_support_state=cls.ANSWER_MODE_BY_SUPPORT_STATE,
            support_assessment_policy_version=cls.SUPPORT_ASSESSMENT_POLICY_VERSION,
            answer_mode_policy_version=cls.ANSWER_MODE_POLICY_VERSION,
            source_navigation_requires_locator=cls.SOURCE_NAVIGATION_REQUIRES_LOCATOR,
            conflict_caps_support_at_partial=cls.CONFLICT_CAPS_SUPPORT_AT_PARTIAL,
            provenance_weakness_caps_support_at_partial=cls.PROVENANCE_WEAKNESS_CAPS_SUPPORT_AT_PARTIAL,
            citation_include_heading_path=cls.CITATION_INCLUDE_HEADING_PATH,
            citation_include_locator=cls.CITATION_INCLUDE_LOCATOR,
        )


def apply_policy_overrides(
    policy: QueryPolicy,
    overrides: QueryPolicyOverride | None,
) -> QueryPolicy:
    """Apply request-scoped overrides onto a base policy."""

    if overrides is None:
        return policy
    merged = policy.model_dump(mode="python")
    merged.update(overrides.model_dump(mode="python", exclude_none=True))
    return QueryPolicy.model_validate(merged)
