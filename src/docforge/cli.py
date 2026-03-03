from __future__ import annotations

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

from docforge import __version__
from docforge.config import load_config
from docforge.connectors import make_connector
from docforge.models import RawDocument


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="docforge", description="Project CLI entrypoint.")
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    subparsers = parser.add_subparsers(dest="command")

    connect_parser = subparsers.add_parser("connect", help="Run connectors and write artifacts.")
    connect_parser.add_argument(
        "--config", required=True, help="Path to connector TOML config file."
    )
    connect_parser.add_argument(
        "--out", required=True, help="Output directory for connector artifacts."
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    if args.command == "connect":
        return _run_connect(config_path=Path(args.config), out_dir=Path(args.out))

    try:
        from rich.console import Console  # type: ignore[import-not-found]

        console = Console(
            force_terminal=False,
            color_system=None,
            markup=False,
            highlight=False,
        )
        console.print("docforge: OK")
    except ModuleNotFoundError:
        print("docforge: OK")
    return 0


def _run_connect(config_path: Path, out_dir: Path) -> int:
    try:
        config = load_config(config_path)
        raw_dir = out_dir / "raw"
        blob_dir = out_dir / "blobs"
        raw_dir.mkdir(parents=True, exist_ok=True)
        blob_dir.mkdir(parents=True, exist_ok=True)

        for source in config.sources:
            connector = make_connector(source)
            for doc in connector.iter_raw_documents():
                _write_document_artifacts(doc=doc, raw_dir=raw_dir, blob_dir=blob_dir)
        return 0
    except Exception as exc:
        print(f"docforge connect error: {exc}", file=sys.stderr)
        return 1


def _write_document_artifacts(doc: RawDocument, raw_dir: Path, blob_dir: Path) -> None:
    doc_key = _doc_key(doc)
    blob_path = blob_dir / f"{doc_key}.bin"
    raw_path = raw_dir / f"{doc_key}.json"
    content_sha256 = sha256(doc.content_bytes).hexdigest()
    blob_path.write_bytes(doc.content_bytes)

    sidecar = _to_sidecar_metadata(doc)
    sidecar["content_sha256"] = content_sha256
    sidecar["content_bytes_len"] = len(doc.content_bytes)
    raw_path.write_text(json.dumps(sidecar, indent=2, sort_keys=True), encoding="utf-8")
    print(
        f"doc_id={doc.doc_id} bytes={len(doc.content_bytes)} sha256={content_sha256} "
        f"raw={raw_path} blob={blob_path}"
    )


def _to_sidecar_metadata(doc: RawDocument) -> dict[str, Any]:
    sidecar = doc.model_dump(mode="json", exclude={"content_bytes"})
    return sidecar


def _doc_key(doc: RawDocument) -> str:
    source_ref = doc.source_ref
    fingerprint = f"{doc.source}|{doc.doc_id}|{source_ref}"
    return sha256(fingerprint.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
