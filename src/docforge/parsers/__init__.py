from __future__ import annotations

from docforge.parsers.canonicalize_html import HtmlCanonicalizer
from docforge.parsers.canonicalize_markdown import MarkdownCanonicalizer
from docforge.parsers.canonicalize_pdf import PdfCanonicalizer
from docforge.parsers.canonicalize_plain import PlainTextCanonicalizer
from docforge.parsers.errors import (
    CanonicalizationError,
    EmptyContentError,
    PdfExtractionError,
    UnsupportedContentTypeError,
)
from docforge.parsers.interfaces import Canonicalizer, Segmenter, StructureExtractor
from docforge.parsers.pipeline import (
    DefaultCanonicalizer,
    DefaultSegmenter,
    DefaultStructureExtractor,
    ParserPipeline,
)
from docforge.parsers.registry import ContentTypeCanonicalizer, default_canonicalizers

__all__ = [
    "CanonicalizationError",
    "Canonicalizer",
    "ContentTypeCanonicalizer",
    "DefaultCanonicalizer",
    "DefaultSegmenter",
    "DefaultStructureExtractor",
    "EmptyContentError",
    "HtmlCanonicalizer",
    "MarkdownCanonicalizer",
    "ParserPipeline",
    "PdfCanonicalizer",
    "PdfExtractionError",
    "PlainTextCanonicalizer",
    "Segmenter",
    "StructureExtractor",
    "UnsupportedContentTypeError",
    "default_canonicalizers",
]
