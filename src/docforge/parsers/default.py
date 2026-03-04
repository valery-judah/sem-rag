from __future__ import annotations

import hashlib

from docforge.connectors.models import RawDocument
from docforge.parsers.base import BaseParser
from docforge.parsers.canonicalize import canonicalize
from docforge.parsers.models import AnchorMap, ParsedDocument
from docforge.parsers.pdf_hybrid.distill import distill_pdf
from docforge.parsers.pdf_hybrid.exceptions import PdfHybridPipelineError
from docforge.parsers.pdf_hybrid.pipeline import run_pdf_pipeline
from docforge.parsers.tree_builder import build_tree


class DeterministicParser(BaseParser):
    """Minimal parser implementation that currently performs canonicalization only."""

    def parse(self, doc: RawDocument) -> ParsedDocument:
        title_meta = doc.metadata.get("title")
        if isinstance(title_meta, str) and title_meta:
            title = title_meta
        else:
            title = doc.source_ref

        pdf_hybrid_fallback = False
        content_bytes = None

        if doc.content_type == "application/pdf" and getattr(
            self.config, "enable_hybrid_pdf_pipeline", False
        ):
            content_bytes = self._materialize_content(doc)
            pipeline_doc = doc.model_copy(update={"content_stream": iter([content_bytes])})
            try:
                extracted_doc = run_pdf_pipeline(pipeline_doc, self.config)
            except (NotImplementedError, PdfHybridPipelineError):
                pdf_hybrid_fallback = True
            else:
                return distill_pdf(extracted_doc, self.config, title=title)

        if content_bytes is None:
            content_bytes = self._materialize_content(doc)

        canon = canonicalize(content_bytes, doc.content_type, self.config.blank_line_collapse)

        metadata = dict(doc.metadata)
        metadata.update(
            {
                "parser_version": self.config.parser_version,
                "content_type": doc.content_type,
                "has_textual_content": canon.has_textual_content,
                "detected_content_family": canon.detected_content_family,
                "canonicalization_warnings": canon.warnings,
            }
        )
        if doc.content_type == "application/pdf" and getattr(
            self.config, "enable_hybrid_pdf_pipeline", False
        ):
            metadata["pdf_hybrid_pipeline_fallback"] = pdf_hybrid_fallback

        return ParsedDocument(
            doc_id=doc.doc_id,
            title=title,
            canonical_text=canon.canonical_text,
            structure_tree=build_tree(canon.canonical_text),
            anchors=AnchorMap(
                doc_anchor=_stable_doc_anchor(doc.doc_id),
                sections=[],
                blocks=[],
            ),
            metadata=metadata,
        )


def _stable_doc_anchor(doc_id: str) -> str:
    return hashlib.sha256(doc_id.encode("utf-8")).hexdigest()[:32]
