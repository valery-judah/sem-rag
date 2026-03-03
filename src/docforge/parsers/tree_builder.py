import re
from collections.abc import Iterator

from docforge.parsers.models import BlockNode, DocNode, HeadingNode, ParserBlockType

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
LIST_RE = re.compile(r"^(?:-\s|\d+\.\s)")
TABLE_RE = re.compile(r"^\|")
CODE_FENCE = "```"


class Token:
    def __init__(self, block_type: str, start: int, end: int, text: str, level: int | None = None):
        self.block_type = block_type
        self.start = start
        self.end = end
        self.text = text
        self.level = level


class BlockTokenizer:
    def __init__(self, text: str):
        self.text = text
        self.lines = text.split("\n")
        self.line_starts = []

        offset = 0
        for line in self.lines:
            self.line_starts.append(offset)
            offset += len(line) + 1  # +1 for \n

    def tokenize(self) -> Iterator[Token]:
        if not self.text:
            return

        idx = 0
        n_lines = len(self.lines)

        while idx < n_lines:
            line = self.lines[idx]

            if not line.strip():
                idx += 1
                continue

            # Heading
            heading_match = HEADING_RE.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                start_offset = self.line_starts[idx]
                end_offset = start_offset + len(line)
                yield Token("HEADING", start_offset, end_offset, heading_text, level)
                idx += 1
                continue

            # Code Block
            if line.startswith(CODE_FENCE):
                start_offset = self.line_starts[idx]
                idx += 1
                while idx < n_lines and not self.lines[idx].startswith(CODE_FENCE):
                    idx += 1

                # Consume the closing fence if we found it
                if idx < n_lines:
                    end_offset = self.line_starts[idx] + len(self.lines[idx])
                    idx += 1
                else:
                    # Unclosed code fence, read to EOF
                    end_offset = len(self.text)

                yield Token(ParserBlockType.CODE.value, start_offset, end_offset, "")
                continue

            # Table
            if TABLE_RE.match(line):
                start_offset = self.line_starts[idx]
                while idx < n_lines and TABLE_RE.match(self.lines[idx]):
                    idx += 1
                end_offset = self.line_starts[idx - 1] + len(self.lines[idx - 1])
                yield Token(ParserBlockType.TABLE.value, start_offset, end_offset, "")
                continue

            # List
            if LIST_RE.match(line):
                start_offset = self.line_starts[idx]
                list_start_idx = idx
                while idx < n_lines and (
                    LIST_RE.match(self.lines[idx])
                    or (
                        self.lines[idx].strip()
                        and not HEADING_RE.match(self.lines[idx])
                        and not TABLE_RE.match(self.lines[idx])
                        and not self.lines[idx].startswith(CODE_FENCE)
                    )
                ):
                    # We continue the list if it's a list item or a continuation of text
                    # (not another block type). For simplicity, standard lists don't interleave
                    # with blanks unless a new block starts. We just group contiguous non-empty
                    # lines that don't start other blocks.
                    # If we hit an empty line, break list.
                    if not self.lines[idx].strip():
                        break
                    if idx > list_start_idx and (
                        HEADING_RE.match(self.lines[idx])
                        or TABLE_RE.match(self.lines[idx])
                        or self.lines[idx].startswith(CODE_FENCE)
                    ):
                        break
                    idx += 1
                end_offset = self.line_starts[idx - 1] + len(self.lines[idx - 1])
                yield Token(ParserBlockType.LIST.value, start_offset, end_offset, "")
                continue

            # Paragraph (anything else)
            start_offset = self.line_starts[idx]
            while (
                idx < n_lines
                and self.lines[idx].strip()
                and not any(
                    [
                        HEADING_RE.match(self.lines[idx]),
                        TABLE_RE.match(self.lines[idx]),
                        LIST_RE.match(self.lines[idx]),
                        self.lines[idx].startswith(CODE_FENCE),
                    ]
                )
            ):
                idx += 1
            end_offset = self.line_starts[idx - 1] + len(self.lines[idx - 1])
            yield Token(ParserBlockType.PARA.value, start_offset, end_offset, "")


def build_tree(canonical_text: str) -> DocNode:
    root = DocNode(children=[])
    if not canonical_text:
        return root

    stack: list[DocNode | HeadingNode] = [root]
    tokenizer = BlockTokenizer(canonical_text)

    for token in tokenizer.tokenize():
        if token.block_type == "HEADING":
            assert token.level is not None
            current_level = token.level

            while len(stack) > 1:
                top = stack[-1]
                assert isinstance(top, HeadingNode)
                if top.level >= current_level:
                    stack.pop()
                else:
                    break

            new_heading = HeadingNode(level=current_level, text=token.text, children=[])
            stack[-1].children.append(new_heading)
            stack.append(new_heading)
        else:
            block_type = ParserBlockType(token.block_type)
            new_block = BlockNode(type=block_type, range=(token.start, token.end))
            stack[-1].children.append(new_block)

    assert isinstance(stack[0], DocNode)
    return stack[0]  # Return root DocNode
