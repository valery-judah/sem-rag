from docforge.segmentation import BlockAnchor, BlockType, SegmentType, TextSpan, segment_document


def create_blocks(spans: list[tuple[int, int]]) -> list[BlockAnchor]:
    return [
        BlockAnchor(
            block_type=BlockType.PARA,
            ref=f"block_{i}",
            span=TextSpan(start_char_offset=start, end_char_offset=end),
        )
        for i, (start, end) in enumerate(spans)
    ]


def test_segment_type_is_passage() -> None:
    canonical_text = "This is a simple test document."
    blocks = create_blocks([(0, len(canonical_text))])

    segments = segment_document(canonical_text, blocks)

    assert len(segments) == 1
    assert segments[0].type == SegmentType.PASSAGE


def test_passage_text_resolves_to_offsets() -> None:
    canonical_text = "Hello world! This is a test."
    blocks = create_blocks([(0, 12), (13, 28)])

    segments = segment_document(canonical_text, blocks)

    assert len(segments) == 2
    for segment in segments:
        expected_text = canonical_text[segment.start_char_offset : segment.end_char_offset]
        assert segment.text == expected_text


def test_no_empty_passages_emitted() -> None:
    canonical_text = "   \n  \t  Block 1.  \n   "
    blocks = create_blocks(
        [(0, 9), (9, 17), (17, 24)]
    )  # 0-9 is whitespace, 9-17 is text, 17-24 is whitespace

    segments = segment_document(canonical_text, blocks)

    assert len(segments) == 1
    assert segments[0].text.strip() == "Block 1."


def test_offsets_strictly_in_bounds() -> None:
    canonical_text = "Short."
    # pass some weird blocks
    blocks = create_blocks([(-1, 3), (0, 0), (2, 20), (0, 6)])

    segments = segment_document(canonical_text, blocks)

    # We expect only blocks that can be strictly bounded and have content
    # (-1, 3) -> should clamp to 0..3 or be rejected? Let's say we clamp and extract.
    # Actually, the test says:
    # `0 <= segment.start_char_offset < segment.end_char_offset <= len(canonical_text)`
    for segment in segments:
        assert 0 <= segment.start_char_offset
        assert segment.start_char_offset < segment.end_char_offset
        assert segment.end_char_offset <= len(canonical_text)
        assert len(segment.text.strip()) > 0
