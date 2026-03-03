from __future__ import annotations

import hashlib

from docforge.connectors.models import RawDocument
from docforge.parsers.base import BaseParser
from docforge.parsers.canonicalize import canonicalize
from docforge.parsers.models import AnchorMap, DocNode, ParsedDocument


class DeterministicParser(BaseParser):
    """Minimal parser implementation that currently performs canonicalization only."""

    def parse(self, doc: RawDocument) -> ParsedDocument:
        content_bytes = self._materialize_content(doc)
        canon = canonicalize(content_bytes, doc.content_type, self.config.blank_line_collapse)

        title_meta = doc.metadata.get("title")
        if isinstance(title_meta, str) and title_meta:
            title = title_meta
        else:
            title = doc.source_ref

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

        return ParsedDocument(
            doc_id=doc.doc_id,
            title=title,
            canonical_text=canon.canonical_text,
            structure_tree=DocNode(children=[]),
            anchors=AnchorMap(
                doc_anchor=_stable_doc_anchor(doc.doc_id),
                sections=[],
                blocks=[],
            ),
            metadata=metadata,
        )


def _stable_doc_anchor(doc_id: str) -> str:
    return hashlib.sha256(doc_id.encode("utf-8")).hexdigest()[:32]
