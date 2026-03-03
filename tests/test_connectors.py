from typing import Any

import pytest
from pydantic import ValidationError

from docforge.connectors.exceptions import (
    ConfigurationError,
    RateLimitError,
    TerminalSourceError,
    TransientSourceError,
)
from docforge.connectors.models import RawDocument


def get_valid_doc_kwargs() -> dict[str, Any]:
    return {
        "doc_id": "test_id_123",
        "source": "test_source",
        "source_ref": "ref_123",
        "url": "http://example.com/doc",
        "content_stream": iter([b"test content"]),
        "content_type": "text/plain",
        "metadata": {"title": "Test Doc"},
        "acl_scope": {"group": "engineering"},
        "timestamps": {"created_at": "2023-01-01T00:00:00Z", "updated_at": "2023-01-02T00:00:00Z"},
    }


def test_raw_document_valid() -> None:
    kwargs = get_valid_doc_kwargs()
    doc = RawDocument(**kwargs)
    assert doc.doc_id == "test_id_123"
    assert doc.source == "test_source"
    assert doc.source_ref == "ref_123"
    assert doc.url == "http://example.com/doc"
    assert list(doc.content_stream) == [b"test content"]
    assert doc.content_type == "text/plain"
    assert doc.metadata == {"title": "Test Doc"}
    assert doc.acl_scope == {"group": "engineering"}
    assert doc.timestamps == {
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-02T00:00:00Z",
    }


@pytest.mark.parametrize(
    "missing_field",
    [
        "doc_id",
        "source",
        "source_ref",
        "url",
        "content_stream",
        "content_type",
        "metadata",
        "acl_scope",
        "timestamps",
    ],
)
def test_raw_document_missing_mandatory_fields(missing_field: str) -> None:
    kwargs = get_valid_doc_kwargs()
    del kwargs[missing_field]
    with pytest.raises(ValidationError):
        RawDocument(**kwargs)


@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("doc_id", ""),
        ("doc_id", 123),
        ("source", ""),
        ("source", 123),
        ("source_ref", ""),
        ("source_ref", 123),
        ("url", 123),
        ("content_stream", "string instead of iterator"),
        ("content_stream", b"bytes instead of iterator"),
        ("content_type", ""),
        ("content_type", 123),
        ("metadata", []),
        ("acl_scope", "not_a_dict"),
        ("timestamps", []),
    ],
)
def test_raw_document_invalid_types_and_values(field: str, invalid_value: Any) -> None:
    kwargs = get_valid_doc_kwargs()
    kwargs[field] = invalid_value
    with pytest.raises(ValidationError):
        RawDocument(**kwargs)


def test_raw_document_strict_mode_rejects_coercion() -> None:
    kwargs = get_valid_doc_kwargs()
    kwargs["timestamps"] = {"created_at": 1, "updated_at": 2}
    with pytest.raises(ValidationError):
        RawDocument(**kwargs)


def test_exception_hierarchies() -> None:
    err_rate = RateLimitError("Rate limited", retry_after=60)
    assert err_rate.retry_after == 60
    assert str(err_rate) == "Rate limited"
    assert isinstance(err_rate, Exception)

    err_config = ConfigurationError("Bad config")
    assert str(err_config) == "Bad config"

    err_transient = TransientSourceError("Network timeout")
    assert str(err_transient) == "Network timeout"

    err_terminal = TerminalSourceError("Not found")
    assert str(err_terminal) == "Not found"
