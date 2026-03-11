"""Structured query interpretation helpers and deterministic interpreter."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
    CorpusSnapshot,
    InterpretedQuery,
    QueryRequest,
    QueryRequestType,
    QuerySpecificity,
    SynthesisMode,
    UnsupportedCapability,
)

_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9\s]+")
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]*")
_T = TypeVar("_T")
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "do",
        "does",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "its",
        "me",
        "of",
        "on",
        "or",
        "show",
        "say",
        "says",
        "tell",
        "that",
        "the",
        "these",
        "this",
        "to",
        "what",
        "where",
        "which",
        "who",
    }
)
_SOURCE_NAVIGATION_PHRASES = (
    "which section",
    "which page",
    "what page",
    "where does",
    "where is",
    "show me where",
    "locate",
    "find the section",
    "find the page",
)
_EXPLANATION_PHRASES = (
    "explain",
    "why ",
    "how does",
    "how do",
    "summarize",
)
_COMPARISON_PHRASES = ("compare", "contrast", "difference between", "vs ", " versus ")
_SYNTHESIS_PHRASES = (
    "synthesize",
    "what do these documents say",
    "across the documents",
    "across these documents",
    "across sources",
)
_CROSS_DOCUMENT_PHRASES = (
    "these documents",
    "across documents",
    "across the documents",
    "across sources",
    "book a and",
    "book b and",
    "my notes and",
)


class RawInterpretedQuery(BaseModel):
    """Strict pre-normalization interpretation payload."""

    model_config = ConfigDict(extra="forbid")

    normalized_question: str = Field(min_length=1)
    request_type: QueryRequestType
    answer_shape: str = Field(min_length=1)
    specificity: QuerySpecificity
    scope_hints: list[str] = Field(default_factory=list)
    synthesis_mode_hint: SynthesisMode = SynthesisMode.NONE
    requires_source_navigation: bool = False
    unsupported_capability_flags: list[UnsupportedCapability] = Field(default_factory=list)
    normalization_notes: list[str] = Field(default_factory=list)


class InterpreterMetadata(BaseModel):
    """Metadata describing the interpreter that produced a result."""

    model_config = ConfigDict(extra="forbid")

    implementation: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    model_id: str | None = None
    normalization_version: str = Field(min_length=1)


class QueryInterpretationResult(BaseModel):
    """Normalized interpretation plus metadata for tracing."""

    model_config = ConfigDict(extra="forbid")

    interpreted_query: InterpretedQuery
    metadata: InterpreterMetadata


class QueryInterpreter(Protocol):
    """Stage-2 interpreter seam."""

    def interpret(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
    ) -> QueryInterpretationResult:
        """Return a normalized interpretation for a query request."""


class DeterministicQueryInterpreter:
    """Deterministic Stage-2 interpreter used for tests and local runs."""

    schema_version = "query.interpretation.v1"
    normalization_version = "deterministic.v1"

    def interpret(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
    ) -> QueryInterpretationResult:
        del snapshot
        raw = _build_raw_interpretation(request.question)
        interpreted = normalize_interpreted_query(raw)
        return QueryInterpretationResult(
            interpreted_query=interpreted,
            metadata=InterpreterMetadata(
                implementation=self.__class__.__name__,
                schema_version=self.schema_version,
                model_id=None,
                normalization_version=self.normalization_version,
            ),
        )


def normalize_interpreted_query(raw: RawInterpretedQuery) -> InterpretedQuery:
    """Normalize a raw interpretation payload into the stable contract."""

    unsupported_flags = _sorted_unique(raw.unsupported_capability_flags)
    scope_hints = _sorted_unique(raw.scope_hints)
    normalization_notes = _sorted_unique(raw.normalization_notes)
    request_type = raw.request_type
    synthesis_mode = raw.synthesis_mode_hint
    if unsupported_flags:
        request_type = QueryRequestType.UNSUPPORTED
        synthesis_mode = SynthesisMode.NONE
    requires_synthesis = synthesis_mode is not SynthesisMode.NONE
    return InterpretedQuery(
        normalized_question=raw.normalized_question,
        request_type=request_type,
        answer_shape=raw.answer_shape,
        specificity=raw.specificity,
        scope_hints=scope_hints,
        requires_synthesis=requires_synthesis,
        synthesis_mode=synthesis_mode,
        requires_source_navigation=raw.requires_source_navigation,
        unsupported_capability_flags=unsupported_flags,
        normalization_notes=normalization_notes,
    )


def _build_raw_interpretation(question: str) -> RawInterpretedQuery:
    normalized_question, normalization_notes = _normalize_question(question)
    request_type = _classify_request_type(normalized_question)
    specificity = _classify_specificity(normalized_question)
    synthesis_mode = _classify_synthesis_mode(normalized_question)
    requires_source_navigation = _requires_source_navigation(normalized_question)
    unsupported_flags = _detect_unsupported_capabilities(normalized_question)
    answer_shape = _derive_answer_shape(
        request_type=request_type,
        specificity=specificity,
        synthesis_mode=synthesis_mode,
        requires_source_navigation=requires_source_navigation,
        unsupported_flags=unsupported_flags,
    )
    return RawInterpretedQuery(
        normalized_question=normalized_question,
        request_type=request_type,
        answer_shape=answer_shape,
        specificity=specificity,
        scope_hints=_extract_scope_hints(normalized_question),
        synthesis_mode_hint=synthesis_mode,
        requires_source_navigation=requires_source_navigation,
        unsupported_capability_flags=unsupported_flags,
        normalization_notes=normalization_notes,
    )


def _normalize_question(question: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    stripped = question.strip()
    if stripped != question:
        notes.append("trimmed_whitespace")
    collapsed = _WHITESPACE_RE.sub(" ", stripped)
    if collapsed != stripped:
        notes.append("collapsed_whitespace")
    without_terminal = collapsed.rstrip("?.! ")
    if without_terminal != collapsed:
        notes.append("trimmed_terminal_punctuation")
    lowered = without_terminal.lower()
    if lowered != without_terminal:
        notes.append("lowercased")
    return lowered, notes


def _classify_request_type(normalized_question: str) -> QueryRequestType:
    if _detect_unsupported_capabilities(normalized_question):
        return QueryRequestType.UNSUPPORTED
    if _requires_source_navigation(normalized_question):
        return QueryRequestType.SOURCE_NAVIGATION
    if any(phrase in normalized_question for phrase in _COMPARISON_PHRASES):
        return QueryRequestType.COMPARISON
    if any(phrase in normalized_question for phrase in _SYNTHESIS_PHRASES):
        return QueryRequestType.SYNTHESIS
    if any(phrase in normalized_question for phrase in _EXPLANATION_PHRASES):
        return QueryRequestType.EXPLANATION
    return QueryRequestType.FACT_LOOKUP


def _classify_specificity(normalized_question: str) -> QuerySpecificity:
    if any(token in normalized_question for token in ("section", "chapter", "page", "part")):
        return QuerySpecificity.SECTION_SCOPED
    if normalized_question.startswith(("what is", "who is", "when is", "when did", "how many")):
        return QuerySpecificity.PRECISE
    return QuerySpecificity.BROAD


def _classify_synthesis_mode(normalized_question: str) -> SynthesisMode:
    if any(phrase in normalized_question for phrase in _CROSS_DOCUMENT_PHRASES):
        return SynthesisMode.CROSS_DOCUMENT
    if any(phrase in normalized_question for phrase in _COMPARISON_PHRASES):
        return SynthesisMode.CROSS_DOCUMENT
    if any(phrase in normalized_question for phrase in _SYNTHESIS_PHRASES):
        return SynthesisMode.CROSS_DOCUMENT
    return SynthesisMode.NONE


def _requires_source_navigation(normalized_question: str) -> bool:
    return any(phrase in normalized_question for phrase in _SOURCE_NAVIGATION_PHRASES)


def _detect_unsupported_capabilities(normalized_question: str) -> list[UnsupportedCapability]:
    flags: list[UnsupportedCapability] = []
    if any(
        token in normalized_question for token in ("outside the corpus", "latest", "current events")
    ):
        flags.append(UnsupportedCapability.EXTERNAL_KNOWLEDGE)
    if any(
        token in normalized_question
        for token in ("figure", "diagram", "image", "screenshot", "chart")
    ):
        flags.append(UnsupportedCapability.IMAGE_OR_FIGURE_REASONING)
    if "table" in normalized_question:
        flags.append(UnsupportedCapability.TABLE_HEAVY_ANSWERING)
    if "ocr" in normalized_question or "scanned pdf" in normalized_question:
        flags.append(UnsupportedCapability.OCR_REQUIRED)
    return _sorted_unique(flags)


def _derive_answer_shape(
    *,
    request_type: QueryRequestType,
    specificity: QuerySpecificity,
    synthesis_mode: SynthesisMode,
    requires_source_navigation: bool,
    unsupported_flags: list[UnsupportedCapability],
) -> str:
    if unsupported_flags:
        return "capability_boundary_response"
    if requires_source_navigation or request_type is QueryRequestType.SOURCE_NAVIGATION:
        return "source_location"
    if request_type is QueryRequestType.COMPARISON:
        return "qualified_comparison"
    if synthesis_mode is SynthesisMode.CROSS_DOCUMENT:
        return "multi_source_synthesis"
    if (
        request_type is QueryRequestType.EXPLANATION
        and specificity is QuerySpecificity.SECTION_SCOPED
    ):
        return "section_scoped_explanation"
    if request_type is QueryRequestType.EXPLANATION:
        return "explanatory_paragraph"
    return "direct_answer"


def _extract_scope_hints(normalized_question: str) -> list[str]:
    hints: list[str] = []
    for token in _TOKEN_RE.findall(_NON_ALNUM_RE.sub(" ", normalized_question)):
        if len(token) < 4 or token in _STOPWORDS:
            continue
        if token not in hints:
            hints.append(token)
        if len(hints) == 6:
            break
    return hints


def _sorted_unique(values: Iterable[_T]) -> list[_T]:
    unique = {value for value in values}
    return sorted(unique, key=lambda value: str(value))
