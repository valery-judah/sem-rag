from docforge.parsers.pdf_hybrid.engines.marker import adapt_marker_output
from docforge.parsers.pdf_hybrid.engines.miner_u import adapt_mineru_output
from docforge.parsers.pdf_hybrid.models import AssetType, BlockType, ParseStatus


def test_adapt_marker_output():
    raw_marker = {
        "children": [
            {
                "id": "/page/1/Page/366",
                "block_type": "Page",
                "polygon": [[0.0, 0.0], [612.0, 0.0], [612.0, 792.0], [0.0, 792.0]],
                "children": [
                    {
                        "id": "/page/1/SectionHeader/0",
                        "block_type": "SectionHeader",
                        "html": "<h1><i>Main Title</i></h1>",
                        "polygon": [[10.0, 10.0], [100.0, 10.0], [100.0, 30.0], [10.0, 30.0]],
                    },
                    {
                        "id": "/page/1/Text/1",
                        "block_type": "Text",
                        "html": (
                            "<p>A simple paragraph.</p><br/>With a second line "
                            "and an entity &amp; a quote &quot;.</p>"
                        ),
                        "polygon": [[10.0, 40.0], [100.0, 40.0], [100.0, 50.0], [10.0, 50.0]],
                    },
                    {
                        "id": "/page/1/Picture/2",
                        "block_type": "Picture",
                        "html": "",
                        "polygon": [[10.0, 60.0], [50.0, 60.0], [50.0, 100.0], [10.0, 100.0]],
                    },
                ],
            }
        ]
    }

    artifact_ref = "s3://test-bucket/marker/output.json"
    candidates = adapt_marker_output(raw_marker, artifact_ref)

    assert len(candidates) == 1
    page1 = candidates[0]

    assert page1.page_idx == 0  # enumeration-based because page_idx not in dict
    assert page1.status == ParseStatus.OK

    # 2 text blocks (Picture has no text, so it's skipped as a BlockCandidate)
    assert len(page1.blocks) == 2

    # Check provenance
    assert page1.blocks[0].source.engine == "marker"
    assert page1.blocks[0].source.engine_artifact_ref == artifact_ref
    assert page1.blocks[0].source.engine_block_ref == "/page/1/SectionHeader/0"

    # Check normalization
    assert page1.blocks[0].type == BlockType.HEADING
    assert page1.blocks[0].text == "Main Title"
    assert page1.blocks[0].poly == [(10.0, 10.0), (100.0, 10.0), (100.0, 30.0), (10.0, 30.0)]

    assert page1.blocks[1].type == BlockType.PARA
    assert page1.blocks[1].poly == [(10.0, 40.0), (100.0, 40.0), (100.0, 50.0), (10.0, 50.0)]
    assert (
        page1.blocks[1].text
        == 'A simple paragraph.\n\nWith a second line and an entity & a quote ".'
    )

    # Check assets
    assert len(page1.assets) == 1
    assert page1.assets[0].type == AssetType.IMAGE
    assert page1.assets[0].source.engine == "marker"
    assert page1.assets[0].bbox_or_poly == [
        [10.0, 60.0],
        [50.0, 60.0],
        [50.0, 100.0],
        [10.0, 100.0],
    ]

    # Check signals
    assert page1.signals.block_count == 2
    assert page1.signals.asset_count == 1
    assert page1.signals.heading_like_count == 1
    assert page1.signals.has_coords is True


def test_adapt_marker_output_flat():
    raw_marker = {
        "blocks": [
            {
                "id": "/page/1/SectionHeader/0",
                "block_type": "SectionHeader",
                "html": "<h1><i>Flat Title</i></h1>",
                "polygon": [[10.0, 10.0], [100.0, 10.0], [100.0, 30.0], [10.0, 30.0]],
            },
            {
                "id": "/page/2/Text/1",
                "block_type": "Text",
                "html": "<p>Flat paragraph.</p>",
                "polygon": [[10.0, 40.0], [100.0, 40.0], [100.0, 50.0], [10.0, 50.0]],
            },
        ],
        "page_info": {},  # Might be ignored in our logic, but included for realism
    }

    artifact_ref = "s3://test-bucket/marker/output_flat.json"
    candidates = adapt_marker_output(raw_marker, artifact_ref)

    assert len(candidates) == 2
    page1 = candidates[0]
    page2 = candidates[1]

    assert page1.page_idx == 0
    assert page1.status == ParseStatus.OK
    assert len(page1.blocks) == 1
    assert page1.blocks[0].text == "Flat Title"
    assert page1.blocks[0].type == BlockType.HEADING

    assert page2.page_idx == 1
    assert page2.status == ParseStatus.OK
    assert len(page2.blocks) == 1
    assert page2.blocks[0].text == "Flat paragraph."
    assert page2.blocks[0].type == BlockType.PARA


def test_adapt_mineru_output_flat():
    raw_mineru = [
        {
            "id": "blk1",
            "type": "text",
            "text": "Intro",
            "text_level": 1,
            "bbox": [0, 0, 10, 10],
            "page_idx": 0,
        },
        {
            "id": "blk2",
            "type": "table",
            "text": "Header 1 | Header 2\nVal 1 | Val 2",
            "bbox": [0, 20, 10, 30],
            "page_idx": 0,
        },
        {"id": "blk3", "type": "equation", "text": "", "bbox": [0, 40, 10, 50], "page_idx": 0},
    ]

    artifact_ref = "local://mineru/result"
    candidates = adapt_mineru_output(raw_mineru, artifact_ref)

    assert len(candidates) == 1
    page0 = candidates[0]

    assert page0.page_idx == 0
    assert page0.status == ParseStatus.OK

    # Eq block has no text, so it creates an asset but no block
    assert len(page0.blocks) == 2

    assert page0.blocks[0].type == BlockType.PARA
    assert page0.blocks[0].text == "Intro"
    assert page0.blocks[0].source.engine == "mineru"

    assert page0.blocks[1].type == BlockType.TABLE
    assert page0.blocks[1].text == "Header 1 | Header 2\nVal 1 | Val 2"

    assert len(page0.assets) == 2
    # Table creates a TABLE_RENDER asset
    assert page0.assets[0].type == AssetType.TABLE_RENDER
    assert page0.assets[0].source.engine_block_ref == "blk2"

    # Equation creates an EQUATION asset
    assert page0.assets[1].type == AssetType.EQUATION
    assert page0.assets[1].source.engine_block_ref == "blk3"
    assert page0.assets[1].bbox_or_poly == [0, 40, 10, 50]  # Any type, stays list


def test_adapt_mineru_output_dict():
    raw_mineru = {
        "pdf_info": [
            {
                "page_idx": 0,
                "preproc_blocks": [
                    {
                        "type": "text",
                        "bbox": [72.0, 72.0, 523.276, 84.0],
                        "lines": [
                            {
                                "bbox": [72.0, 72.0, 523.276, 84.0],
                                "spans": [
                                    {
                                        "bbox": [72.0, 72.0, 523.276, 84.0],
                                        "content": "This is a sentence.",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }

    artifact_ref = "local://mineru/middle.json"
    candidates = adapt_mineru_output(raw_mineru, artifact_ref)

    assert len(candidates) == 1
    page0 = candidates[0]

    assert page0.page_idx == 0
    assert page0.status == ParseStatus.OK
    assert len(page0.blocks) == 1

    assert page0.blocks[0].type == BlockType.PARA
    assert page0.blocks[0].text == "This is a sentence."
    assert page0.blocks[0].source.engine == "mineru"
