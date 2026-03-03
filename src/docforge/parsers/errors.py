from __future__ import annotations

from collections.abc import Iterable


class CanonicalizationError(ValueError):
    def __init__(
        self,
        *,
        code: str,
        doc_id: str,
        content_type: str,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.doc_id = doc_id
        self.content_type = content_type


class UnsupportedContentTypeError(CanonicalizationError):
    def __init__(
        self, *, doc_id: str, content_type: str, supported_content_types: Iterable[str]
    ) -> None:
        supported = ", ".join(sorted(supported_content_types))
        message = (
            f"Unsupported content type '{content_type}' for doc_id '{doc_id}'. "
            f"Supported content types: {supported}."
        )
        super().__init__(
            code="unsupported_content_type",
            doc_id=doc_id,
            content_type=content_type,
            message=message,
        )


class EmptyContentError(CanonicalizationError):
    def __init__(self, *, doc_id: str, content_type: str) -> None:
        message = f"Empty content payload for doc_id '{doc_id}' and content type '{content_type}'."
        super().__init__(
            code="empty_content",
            doc_id=doc_id,
            content_type=content_type,
            message=message,
        )


class PdfExtractionError(CanonicalizationError):
    def __init__(self, *, doc_id: str, content_type: str, reason: str) -> None:
        message = (
            f"PDF canonicalization failed for doc_id '{doc_id}' and content type "
            f"'{content_type}': {reason}."
        )
        super().__init__(
            code="pdf_extraction_failed",
            doc_id=doc_id,
            content_type=content_type,
            message=message,
        )
        self.reason = reason
