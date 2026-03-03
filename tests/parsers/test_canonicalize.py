from docforge.parsers.canonicalize import canonicalize


def test_markdown_preserves_code_block_indentation_and_table_rows() -> None:
    content = (
        b"# Title\r\n\r\n| Name | Value |\r\n| --- | --- |\r\n| A | 1 |\r\n\r\n"
        b"```python\r\nif True:\r\n    print('x')\r\n```\r\n"
    )
    result = canonicalize(content, "text/markdown", blank_line_collapse=2)

    assert result.detected_content_family == "markdown"
    assert result.has_textual_content is True
    assert "| Name | Value |" in result.canonical_text
    assert "| A | 1 |" in result.canonical_text
    assert "```python\nif True:\n    print('x')\n```" in result.canonical_text


def test_html_converts_to_markdown_like_with_structure() -> None:
    content = b"""
    <html><body>
      <h1>Doc</h1>
      <p>Intro text.</p>
      <ul><li>One</li><li>Two</li></ul>
      <table>
        <tr><th>Col A</th><th>Col B</th></tr>
        <tr><td>X</td><td>Y</td></tr>
      </table>
      <pre><code class="language-python">print('hello')</code></pre>
    </body></html>
    """
    result = canonicalize(content, "text/html", blank_line_collapse=2)

    assert result.detected_content_family == "html"
    assert result.has_textual_content is True
    assert "# Doc" in result.canonical_text
    assert "Intro text." in result.canonical_text
    assert "- One" in result.canonical_text
    assert "- Two" in result.canonical_text
    assert "| Col A | Col B |" in result.canonical_text
    assert "| --- | --- |" in result.canonical_text
    assert "| X | Y |" in result.canonical_text
    assert "```python\nprint('hello')\n```" in result.canonical_text


def test_plain_text_uses_utf8_replacement_deterministically() -> None:
    content = b"prefix\xffsuffix"
    first = canonicalize(content, "text/plain", blank_line_collapse=2)
    second = canonicalize(content, "text/plain", blank_line_collapse=2)

    assert first.canonical_text == "prefix\ufffdsuffix"
    assert first == second


def test_newline_normalization_and_blank_line_collapse() -> None:
    content = b"line1\r\n\r\n\rline2\r\n\r\n\r\nline3\r"
    result = canonicalize(content, "text/plain", blank_line_collapse=1)

    assert result.canonical_text == "line1\n\nline2\n\nline3"


def test_unsupported_content_type_returns_non_textual() -> None:
    result = canonicalize(b"%PDF-1.7", "application/pdf", blank_line_collapse=2)

    assert result.canonical_text == ""
    assert result.has_textual_content is False
    assert result.detected_content_family == "unsupported"
    assert result.warnings


def test_canonicalize_is_deterministic_for_same_input() -> None:
    content = b"## Heading\n\nParagraph\n\n```txt\n A \n```\n"
    expected = canonicalize(content, "text/markdown", blank_line_collapse=2)
    for _ in range(5):
        current = canonicalize(content, "text/markdown", blank_line_collapse=2)
        assert current == expected


def test_html_flushes_trailing_inline_text() -> None:
    content = b"<html><body><div>first</div><span>second</span></body></html>"

    result = canonicalize(content, "text/html", blank_line_collapse=2)

    assert result.canonical_text == "firstsecond"
    assert result.has_textual_content is True


def test_html_table_header_uses_row_with_th_cells() -> None:
    content = b"""
    <table>
      <tr><td>r1c1</td><td>r1c2</td></tr>
      <tr><th>h1</th><th>h2</th></tr>
      <tr><td>r3c1</td><td>r3c2</td></tr>
    </table>
    """

    result = canonicalize(content, "text/html", blank_line_collapse=2)

    assert result.canonical_text == "\n\n".join(
        [
            "| h1 | h2 |",
            "| --- | --- |",
            "| r1c1 | r1c2 |",
            "| r3c1 | r3c2 |",
        ]
    )


def test_empty_text_payloads_are_marked_non_textual() -> None:
    for content_type in ("text/plain", "text/markdown", "text/html"):
        result = canonicalize(b"   \n\n\t", content_type, blank_line_collapse=2)
        assert result.canonical_text == ""
        assert result.has_textual_content is False
