from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from docforge.models import DocumentTimestamps, RawDocument
from docforge.parsers import ContentTypeCanonicalizer, EmptyContentError, PdfExtractionError
from docforge.parsers.errors import UnsupportedContentTypeError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "parsers"
UPDATED_AT = datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC)


def _raw_document(*, fixture_name: str, content_type: str) -> RawDocument:
    return RawDocument(
        doc_id=f"fixture:{fixture_name}",
        source="fixture",
        source_ref=fixture_name,
        url=f"file:{fixture_name}",
        content_bytes=(FIXTURES_DIR / fixture_name).read_bytes(),
        content_type=content_type,
        metadata={},
        timestamps=DocumentTimestamps(created_at=UPDATED_AT, updated_at=UPDATED_AT),
    )


@pytest.mark.parametrize(
    ("fixture_name", "content_type", "expected"),
    [
        ("sample.txt", "text/plain", "Billing line one\nBilling line two\n"),
        (
            "sample.md",
            "text/markdown",
            (
                "# Billing Guide\n\nIntro paragraph.\n\n```python\n"
                "def add(a, b):\n    return a + b\n```\n\n## Retry Policy\n"
                "Retries happen nightly.\n"
            ),
        ),
        (
            "sample.html",
            "text/html",
            (
                "Billing Guide\n"
                "Intro paragraph.\n"
                "def add(a, b):\n"
                "    return a + b\n"
                "Retry Policy\n"
                "- Retry daily\n"
                "- Alert on failure"
            ),
        ),
        ("sample.pdf", "application/pdf", "Fixture PDF line 1\nFixture PDF line 2"),
    ],
)
def test_content_type_canonicalizers_parse_fixtures(
    fixture_name: str, content_type: str, expected: str
) -> None:
    canonicalizer = ContentTypeCanonicalizer()
    document = _raw_document(fixture_name=fixture_name, content_type=content_type)

    canonical_text = canonicalizer.canonicalize(document)

    assert canonical_text == expected


@pytest.mark.parametrize(
    ("fixture_name", "content_type"),
    [
        ("sample.txt", "text/plain"),
        ("sample.md", "text/markdown"),
        ("sample.html", "text/html"),
        ("sample.pdf", "application/pdf"),
    ],
)
def test_canonicalization_is_deterministic_for_supported_fixtures(
    fixture_name: str, content_type: str
) -> None:
    canonicalizer = ContentTypeCanonicalizer()
    document = _raw_document(fixture_name=fixture_name, content_type=content_type)

    first = canonicalizer.canonicalize(document)
    second = canonicalizer.canonicalize(document)

    assert second == first
    assert second.encode("utf-8") == first.encode("utf-8")


def test_unsupported_content_type_returns_typed_error() -> None:
    canonicalizer = ContentTypeCanonicalizer()
    document = RawDocument(
        doc_id="unsupported-doc",
        source="fixture",
        source_ref="unsupported.bin",
        url="file:unsupported.bin",
        content_bytes=b"binary data",
        content_type="application/octet-stream",
        metadata={},
        timestamps=DocumentTimestamps(created_at=UPDATED_AT, updated_at=UPDATED_AT),
    )

    with pytest.raises(UnsupportedContentTypeError) as excinfo:
        canonicalizer.canonicalize(document)

    assert excinfo.value.code == "unsupported_content_type"
    assert excinfo.value.doc_id == "unsupported-doc"
    assert excinfo.value.content_type == "application/octet-stream"


def test_empty_supported_content_returns_typed_error() -> None:
    canonicalizer = ContentTypeCanonicalizer()
    document = RawDocument(
        doc_id="empty-doc",
        source="fixture",
        source_ref="empty.txt",
        url="file:empty.txt",
        content_bytes=b"",
        content_type="text/plain",
        metadata={},
        timestamps=DocumentTimestamps(created_at=UPDATED_AT, updated_at=UPDATED_AT),
    )

    with pytest.raises(EmptyContentError) as excinfo:
        canonicalizer.canonicalize(document)

    assert excinfo.value.code == "empty_content"
    assert excinfo.value.doc_id == "empty-doc"
    assert excinfo.value.content_type == "text/plain"


def test_pdf_invalid_payload_has_explicit_fallback_error() -> None:
    canonicalizer = ContentTypeCanonicalizer()
    document = RawDocument(
        doc_id="bad-pdf",
        source="fixture",
        source_ref="bad.pdf",
        url="file:bad.pdf",
        content_bytes=b"not a pdf stream",
        content_type="application/pdf",
        metadata={},
        timestamps=DocumentTimestamps(created_at=UPDATED_AT, updated_at=UPDATED_AT),
    )

    with pytest.raises(PdfExtractionError) as excinfo:
        canonicalizer.canonicalize(document)

    assert excinfo.value.code == "pdf_extraction_failed"
    assert excinfo.value.reason == "invalid_pdf_header"
