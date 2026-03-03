from __future__ import annotations

from docforge.parsers.anchors import AnchorBuilder, collect_structure_anchors, normalize_anchor_slug
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
from docforge.parsers.structure import HeuristicStructureExtractor

__all__ = [
    "AnchorBuilder",
    "CanonicalizationError",
    "Canonicalizer",
    "ContentTypeCanonicalizer",
    "DefaultCanonicalizer",
    "DefaultSegmenter",
    "DefaultStructureExtractor",
    "EmptyContentError",
    "HtmlCanonicalizer",
    "HeuristicStructureExtractor",
    "MarkdownCanonicalizer",
    "ParserPipeline",
    "PdfCanonicalizer",
    "PdfExtractionError",
    "PlainTextCanonicalizer",
    "Segmenter",
    "StructureExtractor",
    "UnsupportedContentTypeError",
    "collect_structure_anchors",
    "default_canonicalizers",
    "normalize_anchor_slug",
]
