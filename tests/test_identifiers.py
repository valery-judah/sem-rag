from __future__ import annotations

import pytest

from doc_forge.identifiers import (
    parse_doc_id,
    parse_workspace_id,
)
from doc_forge.query import CorpusSnapshot, QueryRequest


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("ws-1", "ws-1"),
        ("workspace alpha", "workspace alpha"),
    ],
)
def test_parse_workspace_id_accepts_trimmed_path_safe_values(value: str, expected: str) -> None:
    assert parse_workspace_id(value) == expected


@pytest.mark.parametrize(
    "value",
    ["", " ", " ws-1", "ws-1 ", ".", "..", "team/a", r"team\a"],
)
def test_parse_workspace_id_rejects_empty_whitespace_and_path_shaping_values(value: str) -> None:
    with pytest.raises(ValueError):
        parse_workspace_id(value)


def test_parse_doc_id_accepts_existing_generated_shape() -> None:
    assert parse_doc_id("doc_1234abcd") == "doc_1234abcd"


@pytest.mark.parametrize(
    "value",
    ["", " ", " doc_1234abcd", "doc_1234abcd ", ".", "..", "doc/1", r"doc\1"],
)
def test_parse_doc_id_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        parse_doc_id(value)


def test_query_request_serializes_identifier_fields_as_plain_strings() -> None:
    request = QueryRequest(question="What is indexed?", workspace_id="ws-1")

    assert request.model_dump(mode="json") == {
        "question": "What is indexed?",
        "workspace_id": "ws-1",
        "policy_overrides": None,
    }


def test_corpus_snapshot_serializes_eligible_doc_ids_as_plain_strings() -> None:
    snapshot = CorpusSnapshot(workspace_id="ws-1", eligible_doc_ids=["doc_1234abcd"])

    assert snapshot.model_dump(mode="json")["eligible_doc_ids"] == ["doc_1234abcd"]
