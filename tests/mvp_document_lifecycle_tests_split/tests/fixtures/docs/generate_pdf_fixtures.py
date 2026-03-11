from __future__ import annotations

from pathlib import Path


def write_placeholder_pdf(path: Path, title: str, body_lines: list[str]) -> None:
    # This is a lightweight placeholder generator for the bundle.
    # Replace with reportlab or committed binary fixtures in the real repo.
    lines = ["%PDF-1.4", f"% {title}"] + [f"% {line}" for line in body_lines] + ["%%EOF"]
    path.write_bytes(("\n".join(lines)).encode("utf-8"))


def main() -> None:
    root = Path(__file__).parent
    write_placeholder_pdf(
        root / "text_layer_ok.pdf",
        "text layer ok",
        ["1 Introduction", "Document lifecycle preserves persisted evidence."],
    )
    write_placeholder_pdf(
        root / "sparse_text_layer.pdf",
        "sparse text layer",
        ["Header", "x", "", "Footer"],
    )
    (root / "malformed.pdf").write_bytes(b"%PDF-1.4\nbroken")
    (root / "unsupported.png").write_bytes(b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    main()
