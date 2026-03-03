from docforge.parsers.models import BlockNode, DocNode, HeadingNode, ParserBlockType
from docforge.parsers.tree_builder import BlockTokenizer, build_tree


def test_tokenizer_headings():
    text = "# H1\n## H2\n### H3"
    tokenizer = BlockTokenizer(text)
    tokens = list(tokenizer.tokenize())

    assert len(tokens) == 3
    assert tokens[0].block_type == "HEADING"
    assert tokens[0].level == 1
    assert tokens[0].text == "H1"

    assert tokens[1].block_type == "HEADING"
    assert tokens[1].level == 2
    assert tokens[1].text == "H2"

    assert tokens[2].block_type == "HEADING"
    assert tokens[2].level == 3
    assert tokens[2].text == "H3"


def test_tokenizer_mixed_blocks():
    text = """# Title

This is a para.

- list item 1
- list item 2

```python
print("Hello")
```

| col1 | col2 |
|---|---|
| a | b |
"""
    tokenizer = BlockTokenizer(text)
    tokens = list(tokenizer.tokenize())

    assert len(tokens) == 5
    assert tokens[0].block_type == "HEADING"
    assert tokens[0].text == "Title"
    assert tokens[1].block_type == ParserBlockType.PARA
    assert tokens[2].block_type == ParserBlockType.LIST
    assert tokens[3].block_type == ParserBlockType.CODE
    assert tokens[4].block_type == ParserBlockType.TABLE


def test_build_tree_hierarchy_integrity():
    # Scenario: Parse text with H1 -> H2 -> H3 -> H2.
    text = """# H1
## H2_1
### H3
## H2_2
"""
    tree = build_tree(text)

    assert len(tree.children) == 1
    h1 = tree.children[0]
    assert isinstance(h1, HeadingNode) and h1.level == 1

    assert len(h1.children) == 2
    h2_1, h2_2 = h1.children

    assert isinstance(h2_1, HeadingNode) and h2_1.level == 2
    assert isinstance(h2_2, HeadingNode) and h2_2.level == 2

    assert len(h2_1.children) == 1
    h3 = h2_1.children[0]
    assert isinstance(h3, HeadingNode) and h3.level == 3

    assert len(h2_2.children) == 0


def test_build_tree_no_headings():
    # Scenario: Document without headings.
    text = """Para 1.

Para 2.

- List
"""
    tree = build_tree(text)

    assert len(tree.children) == 3
    for child in tree.children:
        assert isinstance(child, BlockNode)

    assert tree.children[0].type == ParserBlockType.PARA
    assert tree.children[1].type == ParserBlockType.PARA
    assert tree.children[2].type == ParserBlockType.LIST


def test_build_tree_skipped_levels():
    # Scenario: H1 followed by H4.
    text = """# H1
#### H4
"""
    tree = build_tree(text)

    assert len(tree.children) == 1
    h1 = tree.children[0]
    assert isinstance(h1, HeadingNode) and h1.level == 1

    assert len(h1.children) == 1
    h4 = h1.children[0]
    assert isinstance(h4, HeadingNode) and h4.level == 4


def test_build_tree_empty_doc():
    text = ""
    tree = build_tree(text)
    assert isinstance(tree, DocNode)
    assert len(tree.children) == 0


def test_build_tree_block_counts():
    text = """# Title

Para

- list

```
code
```

| a |
|---|
"""
    tree = build_tree(text)

    def count_blocks(node, block_type):
        count = 0
        for child in node.children:
            if isinstance(child, BlockNode) and child.type == block_type:
                count += 1
            elif isinstance(child, HeadingNode):
                count += count_blocks(child, block_type)
        return count

    assert count_blocks(tree, ParserBlockType.PARA) == 1
    assert count_blocks(tree, ParserBlockType.LIST) == 1
    assert count_blocks(tree, ParserBlockType.CODE) == 1
    assert count_blocks(tree, ParserBlockType.TABLE) == 1
