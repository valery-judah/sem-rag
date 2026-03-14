"""Shared validated identifier types used across runtime seams."""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, Field


def _validate_identifier(
    value: str,
    *,
    field_name: str,
    reject_dot_segments: bool,
) -> str:
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if "/" in value or "\\" in value:
        raise ValueError(f"{field_name} must not contain path separators")
    if reject_dot_segments and value in {".", ".."}:
        raise ValueError(f"{field_name} must not be '.' or '..'")
    return value


def validate_workspace_id(value: str) -> str:
    """Validate a workspace identifier."""

    return _validate_identifier(
        value,
        field_name="workspace_id",
        reject_dot_segments=True,
    )


def validate_doc_id(value: str) -> str:
    """Validate a document identifier."""

    return _validate_identifier(
        value,
        field_name="doc_id",
        reject_dot_segments=True,
    )


def validate_query_id(value: str) -> str:
    """Validate a query identifier."""

    return _validate_identifier(
        value,
        field_name="query_id",
        reject_dot_segments=True,
    )


WorkspaceId = Annotated[str, Field(min_length=1), AfterValidator(validate_workspace_id)]
DocId = Annotated[str, Field(min_length=1), AfterValidator(validate_doc_id)]
QueryId = Annotated[str, Field(min_length=1), AfterValidator(validate_query_id)]


def parse_workspace_id(value: str) -> WorkspaceId:
    """Validate and cast a workspace identifier for non-Pydantic call sites."""

    return validate_workspace_id(value)


def parse_doc_id(value: str) -> DocId:
    """Validate and cast a document identifier for non-Pydantic call sites."""

    return validate_doc_id(value)


def parse_query_id(value: str) -> QueryId:
    """Validate and cast a query identifier for non-Pydantic call sites."""

    return validate_query_id(value)


__all__ = [
    "DocId",
    "QueryId",
    "WorkspaceId",
    "parse_doc_id",
    "parse_query_id",
    "parse_workspace_id",
    "validate_doc_id",
    "validate_query_id",
    "validate_workspace_id",
]
