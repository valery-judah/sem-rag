"""Recover document sections from normalized artifacts."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from doc_forge.artifacts import NormalizedArtifact, NormalizedArtifactBlock
from doc_forge.corpus import Section, SourceType
from doc_forge.persistence import PersistedDocument


@dataclass(slots=True)
class _OpenSection:
    section: Section
    last_page: int | None
    last_offset: int | None


class SectionDerivationService:
    """Build stable section records from normalized block structure."""

    def derive(
        self,
        *,
        document: PersistedDocument,
        artifact: NormalizedArtifact,
    ) -> list[Section]:
        if document.source_type is SourceType.MARKDOWN:
            sections = self._derive_markdown(document=document, artifact=artifact)
        else:
            sections = self._derive_pdf(document=document, artifact=artifact)
        if not sections:
            return [
                Section(
                    section_id=f"{document.doc_id}:section:0",
                    doc_id=document.doc_id,
                    heading_path=[document.title],
                    depth=0,
                    heading_text=document.title,
                    structure_confidence=0.1,
                )
            ]
        return sections

    def _derive_markdown(
        self,
        *,
        document: PersistedDocument,
        artifact: NormalizedArtifact,
    ) -> list[Section]:
        sections: list[_OpenSection] = []
        stack: list[tuple[int, Section]] = []
        synthetic_root = self._make_section(
            document=document,
            ordinal=0,
            heading_path=[document.title],
            parent_section_id=None,
            heading_text=document.title,
            first_block=None,
            confidence=0.25,
        )
        sections.append(_OpenSection(section=synthetic_root, last_page=None, last_offset=None))
        stack.append((0, synthetic_root))
        next_ordinal = 1

        for block in sorted(artifact.blocks, key=lambda item: item.order_index):
            if block.kind == "heading":
                heading_level = max(getattr(block, "heading_level", None) or 1, 1)
                while stack and stack[-1][0] >= heading_level:
                    stack.pop()
                parent = stack[-1][1] if stack else None
                if parent is None:
                    heading_path = [block.text]
                    parent_section_id = None
                else:
                    heading_path = [*parent.heading_path, block.text]
                    parent_section_id = parent.section_id
                section = self._make_section(
                    document=document,
                    ordinal=next_ordinal,
                    heading_path=heading_path,
                    parent_section_id=parent_section_id,
                    heading_text=block.text,
                    first_block=block,
                    confidence=1.0,
                )
                sections.append(
                    _OpenSection(section=section, last_page=block.page_number, last_offset=None)
                )
                stack.append((heading_level, section))
                next_ordinal += 1
                continue

            current = stack[-1][1]
            self._extend_section(
                sections=sections,
                section_id=current.section_id,
                block=block,
            )

        return [item.section for item in sections]

    def _derive_pdf(
        self,
        *,
        document: PersistedDocument,
        artifact: NormalizedArtifact,
    ) -> list[Section]:
        by_heading: dict[tuple[str, ...], _OpenSection] = {}
        by_page: defaultdict[int | None, list[NormalizedArtifactBlock]] = defaultdict(list)
        for block in sorted(artifact.blocks, key=lambda item: item.order_index):
            by_page[block.page_number].append(block)

        sections: list[Section] = []
        ordinal = 0
        for page_number, blocks in by_page.items():
            heading_blocks = [block for block in blocks if block.kind == "heading"]
            if heading_blocks:
                for block in heading_blocks:
                    heading_path = block.heading_path or [document.title, block.text]
                    key = tuple(heading_path)
                    if key in by_heading:
                        self._extend_section_block(by_heading[key], block)
                        continue
                    section = self._make_section(
                        document=document,
                        ordinal=ordinal,
                        heading_path=heading_path,
                        parent_section_id=None,
                        heading_text=heading_path[-1],
                        first_block=block,
                        confidence=0.6,
                    )
                    open_section = _OpenSection(
                        section=section,
                        last_page=block.page_number,
                        last_offset=block.source_end_offset,
                    )
                    by_heading[key] = open_section
                    sections.append(section)
                    ordinal += 1
            else:
                heading_text = f"Page {page_number}" if page_number is not None else document.title
                heading_path = [document.title, heading_text]
                section = self._make_section(
                    document=document,
                    ordinal=ordinal,
                    heading_path=heading_path,
                    parent_section_id=None,
                    heading_text=heading_text,
                    first_block=blocks[0] if blocks else None,
                    confidence=0.3,
                )
                for block in blocks:
                    self._extend_section_values(section, block)
                sections.append(section)
                ordinal += 1
        return sections

    def _make_section(
        self,
        *,
        document: PersistedDocument,
        ordinal: int,
        heading_path: list[str],
        parent_section_id: str | None,
        heading_text: str,
        first_block: NormalizedArtifactBlock | None,
        confidence: float,
    ) -> Section:
        return Section(
            section_id=f"{document.doc_id}:section:{ordinal}",
            doc_id=document.doc_id,
            heading_path=heading_path,
            depth=max(len(heading_path) - 1, 0),
            parent_section_id=parent_section_id,
            heading_text=heading_text,
            page_start=first_block.page_number if first_block is not None else None,
            page_end=first_block.page_number if first_block is not None else None,
            source_start_offset=first_block.source_start_offset
            if first_block is not None
            else None,
            source_end_offset=first_block.source_end_offset if first_block is not None else None,
            structure_confidence=confidence,
        )

    def _extend_section(
        self,
        *,
        sections: list[_OpenSection],
        section_id: str,
        block: NormalizedArtifactBlock,
    ) -> None:
        for item in sections:
            if item.section.section_id == section_id:
                self._extend_section_block(item, block)
                return

    def _extend_section_block(
        self, open_section: _OpenSection, block: NormalizedArtifactBlock
    ) -> None:
        self._extend_section_values(open_section.section, block)
        open_section.last_page = block.page_number
        open_section.last_offset = block.source_end_offset

    def _extend_section_values(self, section: Section, block: NormalizedArtifactBlock) -> None:
        if block.page_number is not None:
            if section.page_start is None:
                section.page_start = block.page_number
            section.page_end = block.page_number
        if block.source_start_offset is not None and section.source_start_offset is None:
            section.source_start_offset = block.source_start_offset
        if block.source_end_offset is not None:
            section.source_end_offset = block.source_end_offset
