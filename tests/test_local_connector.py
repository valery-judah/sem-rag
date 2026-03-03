from pathlib import Path

from docforge.connectors.exceptions import ConfigurationError
from docforge.connectors.local import LocalFileConnector


def test_local_file_connector_init(tmp_path: Path) -> None:
    connector = LocalFileConnector({"base_dir": str(tmp_path)})
    assert connector.base_dir == tmp_path.resolve()

    try:
        LocalFileConnector({"base_dir": "/does_not_exist_123"})
        raise AssertionError("Should have raised ConfigurationError")
    except ConfigurationError as e:
        assert "does not exist or is not a directory" in str(e)


def test_local_file_connector_fetching(tmp_path: Path) -> None:
    file1 = tmp_path / "test1.txt"
    file1.write_text("Hello World")

    file2 = tmp_path / "test2.pdf"
    file2.write_bytes(b"%PDF-1.4\n1 0 obj\n")

    file3 = tmp_path / "ignore.tmp"
    file3.write_text("ignore me")

    config = {
        "base_dir": str(tmp_path),
        "name": "local_test",
        "include_globs": ["*.txt", "*.pdf"],
        "exclude_globs": ["*.tmp"],
    }

    connector = LocalFileConnector(config)

    doc_iter = connector.fetch_documents()
    docs = list(doc_iter)

    assert len(docs) == 2

    docs_by_ref = {d[0].source_ref: d[0] for d in docs}

    txt_doc = docs_by_ref["test1.txt"]
    assert txt_doc.content_type == "text/plain"
    assert b"".join(txt_doc.content_stream) == b"Hello World"

    pdf_doc = docs_by_ref["test2.pdf"]
    assert pdf_doc.content_type == "application/pdf"
    assert b"".join(pdf_doc.content_stream) == b"%PDF-1.4\n1 0 obj\n"


def test_local_file_connector_deterministic_id(tmp_path: Path) -> None:
    file1 = tmp_path / "test1.txt"
    file1.write_text("Hello World")

    connector1 = LocalFileConnector({"base_dir": str(tmp_path), "name": "sourceA"})
    doc1, _ = next(connector1.fetch_documents())

    connector2 = LocalFileConnector({"base_dir": str(tmp_path), "name": "sourceA"})
    doc2, _ = next(connector2.fetch_documents())

    assert doc1.doc_id == doc2.doc_id

    connector3 = LocalFileConnector({"base_dir": str(tmp_path), "name": "sourceB"})
    doc3, _ = next(connector3.fetch_documents())

    # After refactor, ID is based on "local" and source_ref, not source_name.
    assert doc3.doc_id == doc1.doc_id


def test_local_file_connector_incremental(tmp_path: Path) -> None:
    file1 = tmp_path / "test1.txt"
    file1.write_text("Hello")

    connector = LocalFileConnector({"base_dir": str(tmp_path)})

    docs_and_cursors = list(connector.fetch_documents())
    assert len(docs_and_cursors) == 1

    _, next_cursor = docs_and_cursors[-1]

    # Write a new file
    file2 = tmp_path / "test2.txt"
    file2.write_text("World")

    # We might need to make sure the mtime is definitely greater
    # but practically writing after the first fetch should be later or equal
    # Let's just adjust file2's mtime to be strictly greater
    import os

    os.utime(file2, (next_cursor + 10, next_cursor + 10))

    new_docs = list(connector.fetch_documents(cursor=next_cursor + 5))
    assert len(new_docs) == 1
    assert new_docs[0][0].source_ref == "test2.txt"
