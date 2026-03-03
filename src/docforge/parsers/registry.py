from __future__ import annotations

from collections.abc import Mapping

from docforge.models import RawDocument
from docforge.parsers.canonicalize_html import HtmlCanonicalizer
from docforge.parsers.canonicalize_markdown import MarkdownCanonicalizer
from docforge.parsers.canonicalize_pdf import PdfCanonicalizer
from docforge.parsers.canonicalize_plain import PlainTextCanonicalizer
from docforge.parsers.errors import UnsupportedContentTypeError
from docforge.parsers.interfaces import Canonicalizer


class ContentTypeCanonicalizer:
    def __init__(self, canonicalizers: Mapping[str, Canonicalizer] | None = None) -> None:
        self._canonicalizers = dict(
            canonicalizers if canonicalizers is not None else default_canonicalizers()
        )

    def canonicalize(self, document: RawDocument) -> str:
        canonicalizer = self._canonicalizers.get(document.content_type)
        if canonicalizer is None:
            raise UnsupportedContentTypeError(
                doc_id=document.doc_id,
                content_type=document.content_type,
                supported_content_types=self._canonicalizers.keys(),
            )
        return canonicalizer.canonicalize(document)


def default_canonicalizers() -> dict[str, Canonicalizer]:
    return {
        "text/plain": PlainTextCanonicalizer(),
        "text/markdown": MarkdownCanonicalizer(),
        "text/html": HtmlCanonicalizer(),
        "application/pdf": PdfCanonicalizer(),
    }
