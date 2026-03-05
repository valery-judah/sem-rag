from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
import tomllib
import unicodedata
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from docforge.experiment.config import VariantConfig
from docforge.experiment.extractors import ExtractedPage, build_extractor
from docforge.experiment.models import ParsedChunk, ParsedDocument, ParsedPage


@dataclass(slots=True)
class RunResult:
    run_id: str
    output_dir: Path
    manifest_path: Path
    parsed_document_path: Path
    chunks_markdown_path: Path


@dataclass(slots=True)
class ExtractionSummary:
    selected_pages: list[ExtractedPage]
    page_extractors: dict[int, str]
    router_decisions: list[dict[str, Any]]
    extractor_errors: dict[str, str]


def run_baseline_pipeline(
    *,
    source_path: Path,
    variant: VariantConfig,
    output_root: Path,
) -> RunResult:
    if not source_path.exists():
        raise FileNotFoundError(f"Input file was not found: {source_path}")

    started_at = datetime.now(tz=UTC)
    started_monotonic = time.perf_counter()
    extraction = _run_extraction_with_routing(source_path=source_path, variant=variant)

    parsed_pages: list[ParsedPage] = []

    for extracted_page in extraction.selected_pages:
        canonical_text = _normalize_text(extracted_page.text, variant)
        parsed_pages.append(
            ParsedPage(
                page_index=extracted_page.page_index,
                width=extracted_page.width,
                height=extracted_page.height,
                canonical_text=canonical_text,
            )
        )

    if variant.postprocess.strip_repeated_margin_boilerplate:
        _strip_repeated_margin_boilerplate(parsed_pages)

    doc_id = _build_doc_id(source_path)
    chunks = _build_chunks(
        doc_id=doc_id,
        pages=parsed_pages,
        variant=variant,
        page_extractors=extraction.page_extractors,
    )
    parsed_document = ParsedDocument(
        doc_id=doc_id,
        source_uri=str(source_path),
        page_count=len(parsed_pages),
        pages=parsed_pages,
        chunks=chunks,
    )

    elapsed_seconds = time.perf_counter() - started_monotonic
    completed_at = datetime.now(tz=UTC)

    metrics = _compute_metrics(parsed_document=parsed_document, elapsed_seconds=elapsed_seconds)
    needles_report = {
        "summary": {
            "total_needles": 0,
            "found_in_canonical_text": 0,
            "found_in_chunks": 0,
            "bm25_top_k_supported": False,
        },
        "needles": [],
    }
    gold_eval = {
        "gold_pages": [],
        "notes": "Baseline pipeline does not include gold annotations yet.",
    }

    run_id = started_at.strftime("%Y%m%dT%H%M%SZ")
    output_dir = output_root / run_id / variant.variant_id / source_path.stem

    parsed_document_path = output_dir / "parsed_document.json"
    chunks_path = output_dir / "chunks.jsonl"
    router_path = output_dir / "router_decisions.jsonl"
    metrics_path = output_dir / "metrics.json"
    needles_path = output_dir / "needles_report.json"
    gold_eval_path = output_dir / "gold_eval.json"
    human_review_path = output_dir / "human_review.csv"
    manifest_path = output_dir / "run_manifest.json"
    chunks_markdown_path = output_dir / "chunks_review.md"

    _write_json(parsed_document_path, parsed_document.to_dict())
    _write_jsonl(chunks_path, [asdict(chunk) for chunk in chunks])
    _write_jsonl(router_path, extraction.router_decisions)
    _write_json(metrics_path, metrics)
    _write_json(needles_path, needles_report)
    _write_json(gold_eval_path, gold_eval)
    _write_text(human_review_path, "page_index,variant_a,variant_b,winner,issue_tags,notes\n")
    _write_chunks_markdown(
        path=chunks_markdown_path,
        parsed_document=parsed_document,
        variant=variant,
    )

    run_manifest = {
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "duration_seconds": elapsed_seconds,
        "git_sha": _git_sha(),
        "variant_config": asdict(variant),
        "source": {
            "path": str(source_path),
            "checksum_sha256": _sha256_file(source_path),
        },
        "runtime": {
            "page_count": len(parsed_pages),
            "seconds_per_page": elapsed_seconds / max(1, len(parsed_pages)),
            "p95_seconds_per_page": elapsed_seconds / max(1, len(parsed_pages)),
        },
        "failures": {
            "count": len(extraction.extractor_errors),
            "reasons": [
                {"extractor": extractor_name, "error": reason}
                for extractor_name, reason in sorted(extraction.extractor_errors.items())
            ],
        },
    }
    _write_json(manifest_path, run_manifest)

    return RunResult(
        run_id=run_id,
        output_dir=output_dir,
        manifest_path=manifest_path,
        parsed_document_path=parsed_document_path,
        chunks_markdown_path=chunks_markdown_path,
    )


def _run_extraction_with_routing(*, source_path: Path, variant: VariantConfig) -> ExtractionSummary:
    extractor_chain = _resolve_extractor_chain(variant)
    extractor_outputs, extractor_errors = _collect_extractor_outputs(
        source_path=source_path,
        extractor_chain=extractor_chain,
        variant=variant,
    )

    if variant.extractor.strip().lower() == "hybrid" and "pypdf" not in extractor_outputs:
        try:
            quick_pages_list = build_extractor("pypdf").extract(source_path)
            extractor_outputs["pypdf"] = {page.page_index: page for page in quick_pages_list}
        except Exception as exc:
            extractor_errors.setdefault("pypdf", str(exc))
        if "pypdf" not in extractor_chain:
            extractor_chain.append("pypdf")

    page_count = _page_count(extractor_outputs)
    if page_count == 0:
        if extractor_errors:
            reasons = "; ".join(
                f"{extractor_name}: {error}"
                for extractor_name, error in sorted(extractor_errors.items())
            )
            raise RuntimeError(f"No extractor produced output pages. Failures: {reasons}")
        raise RuntimeError("No extractor produced output pages.")

    min_tokens = _routing_int(variant.routing.get("min_tokens"), default=25, minimum=0)
    scan_char_threshold = _routing_int(
        variant.routing.get("scan_char_threshold"),
        default=80,
        minimum=1,
    )

    default_order = _filter_routing_order(
        _normalize_extractor_list(variant.routing.get("default_order")),
        fallback=extractor_chain,
    )
    scan_likely_order = _filter_routing_order(
        _normalize_extractor_list(variant.routing.get("scan_likely_order")),
        fallback=default_order,
    )

    quick_pages = extractor_outputs.get("pypdf", {})
    selected_pages: list[ExtractedPage] = []
    page_extractors: dict[int, str] = {}
    router_decisions: list[dict[str, Any]] = []

    for page_index in range(page_count):
        quick_page = quick_pages.get(page_index)
        quick_char_count = len((quick_page.text if quick_page is not None else "").strip())
        scan_likely = quick_char_count < scan_char_threshold
        route_order = scan_likely_order if scan_likely else default_order

        selected_page, selected_extractor, fallback_reason = _select_page_for_route(
            page_index=page_index,
            route_order=route_order,
            extractor_outputs=extractor_outputs,
            extractor_errors=extractor_errors,
            min_tokens=min_tokens,
        )
        selected_pages.append(selected_page)
        page_extractors[page_index] = selected_extractor

        char_count_by_extractor: dict[str, int] = {}
        for extractor_name in extractor_chain:
            page = extractor_outputs.get(extractor_name, {}).get(page_index)
            if page is None:
                continue
            char_count_by_extractor[extractor_name] = len(page.text.strip())

        router_decisions.append(
            {
                "page_index": page_index,
                "extractor": selected_extractor,
                "features": {
                    "quick_text_char_count": quick_char_count,
                    "scan_likely": scan_likely,
                    "char_count_by_extractor": char_count_by_extractor,
                },
                "fallback_chain": route_order,
                "fallback_reason": fallback_reason,
                "extractor_errors": {
                    extractor_name: extractor_errors[extractor_name]
                    for extractor_name in route_order
                    if extractor_name in extractor_errors
                },
            }
        )

    return ExtractionSummary(
        selected_pages=selected_pages,
        page_extractors=page_extractors,
        router_decisions=router_decisions,
        extractor_errors=extractor_errors,
    )


def _resolve_extractor_chain(variant: VariantConfig) -> list[str]:
    primary = variant.extractor.strip().lower()
    if primary == "hybrid":
        configured = _normalize_extractor_list(variant.routing.get("extractors"))
        if configured:
            return configured
        return ["mineru", "marker", "pymupdf", "pypdf"]

    fallback_extractors = _normalize_extractor_list(variant.routing.get("fallback_extractors"))
    chain = [primary]
    for fallback_extractor in fallback_extractors:
        if fallback_extractor not in chain:
            chain.append(fallback_extractor)
    return chain


def _normalize_extractor_list(value: Any) -> list[str]:
    if isinstance(value, str):
        candidates = [part.strip() for part in value.split(",")]
    elif isinstance(value, list):
        candidates = [str(part).strip() for part in value]
    else:
        return []

    normalized: list[str] = []
    for candidate in candidates:
        lowered = candidate.lower()
        if not lowered or lowered in normalized:
            continue
        normalized.append(lowered)
    return normalized


def _filter_routing_order(order: list[str], *, fallback: list[str]) -> list[str]:
    if not order:
        return list(fallback)

    fallback_set = set(fallback)
    filtered: list[str] = []
    for extractor_name in order:
        if extractor_name not in fallback_set:
            continue
        if extractor_name in filtered:
            continue
        filtered.append(extractor_name)

    if filtered:
        return filtered
    return list(fallback)


def _collect_extractor_outputs(
    *,
    source_path: Path,
    extractor_chain: list[str],
    variant: VariantConfig,
) -> tuple[dict[str, dict[int, ExtractedPage]], dict[str, str]]:
    outputs: dict[str, dict[int, ExtractedPage]] = {}
    errors: dict[str, str] = {}

    for extractor_name in extractor_chain:
        try:
            extractor_options = _extractor_options_for_variant(variant, extractor_name)
            extractor = build_extractor(extractor_name, options=extractor_options)
            pages = extractor.extract(source_path)
        except Exception as exc:
            errors[extractor_name] = str(exc)
            continue

        pages_by_index = {page.page_index: page for page in pages}
        outputs[extractor_name] = pages_by_index

    return outputs, errors


def _extractor_options_for_variant(variant: VariantConfig, extractor_name: str) -> dict[str, Any]:
    options: dict[str, Any] = {}

    extractor_options_raw = variant.routing.get("extractor_options")
    if isinstance(extractor_options_raw, dict):
        selected = extractor_options_raw.get(extractor_name)
        if isinstance(selected, dict):
            options.update(selected)

    config_path_value = options.get("config_path")
    if isinstance(config_path_value, str) and config_path_value.strip():
        config_options = _load_extractor_options_file(Path(config_path_value.strip()))
        merged = dict(config_options)
        merged.update({key: value for key, value in options.items() if key != "config_path"})
        options = merged

    return options


def _load_extractor_options_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Extractor options config not found: {path}")

    suffix = path.suffix.lower()
    content = path.read_text(encoding="utf-8")

    if suffix == ".json":
        parsed = json.loads(content)
    elif suffix == ".toml":
        parsed = tomllib.loads(content)
    else:
        raise ValueError(f"Unsupported extractor options config format '{path.suffix}' for {path}.")

    if not isinstance(parsed, dict):
        raise ValueError(f"Extractor options config must be a mapping: {path}")
    return parsed


def _page_count(extractor_outputs: dict[str, dict[int, ExtractedPage]]) -> int:
    max_page_index = -1
    for pages in extractor_outputs.values():
        if not pages:
            continue
        max_page_index = max(max_page_index, max(pages))
    return max_page_index + 1


def _routing_int(value: Any, *, default: int, minimum: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return max(minimum, value)
    if isinstance(value, str):
        try:
            parsed = int(value.strip())
        except ValueError:
            return default
        return max(minimum, parsed)
    return default


def _select_page_for_route(
    *,
    page_index: int,
    route_order: list[str],
    extractor_outputs: dict[str, dict[int, ExtractedPage]],
    extractor_errors: dict[str, str],
    min_tokens: int,
) -> tuple[ExtractedPage, str, str | None]:
    primary = route_order[0] if route_order else None

    for extractor_name in route_order:
        page = extractor_outputs.get(extractor_name, {}).get(page_index)
        if page is None:
            continue
        if len(page.text.split()) >= min_tokens:
            fallback_reason = _build_fallback_reason(
                primary=primary,
                selected=extractor_name,
                page_index=page_index,
                extractor_outputs=extractor_outputs,
                extractor_errors=extractor_errors,
            )
            return page, extractor_name, fallback_reason

    for extractor_name in route_order:
        page = extractor_outputs.get(extractor_name, {}).get(page_index)
        if page is None or not page.text.strip():
            continue
        fallback_reason = _build_fallback_reason(
            primary=primary,
            selected=extractor_name,
            page_index=page_index,
            extractor_outputs=extractor_outputs,
            extractor_errors=extractor_errors,
        )
        return page, extractor_name, fallback_reason

    for extractor_name in route_order:
        page = extractor_outputs.get(extractor_name, {}).get(page_index)
        if page is None:
            continue
        fallback_reason = _build_fallback_reason(
            primary=primary,
            selected=extractor_name,
            page_index=page_index,
            extractor_outputs=extractor_outputs,
            extractor_errors=extractor_errors,
        )
        return page, extractor_name, fallback_reason

    empty_page = ExtractedPage(page_index=page_index, text="")
    fallback_reason = None
    if primary:
        fallback_reason = _build_fallback_reason(
            primary=primary,
            selected=primary,
            page_index=page_index,
            extractor_outputs=extractor_outputs,
            extractor_errors=extractor_errors,
        )
    return empty_page, primary or "none", fallback_reason


def _build_fallback_reason(
    *,
    primary: str | None,
    selected: str,
    page_index: int,
    extractor_outputs: dict[str, dict[int, ExtractedPage]],
    extractor_errors: dict[str, str],
) -> str | None:
    if primary is None or selected == primary:
        return None

    if primary in extractor_errors:
        return f"primary extractor '{primary}' failed: {extractor_errors[primary]}"

    primary_page = extractor_outputs.get(primary, {}).get(page_index)
    if primary_page is None:
        return f"primary extractor '{primary}' did not return page {page_index}"

    return f"primary extractor '{primary}' returned low-content page {page_index}"


def _normalize_text(text: str, variant: VariantConfig) -> str:
    normalized = unicodedata.normalize("NFKC", text.replace("\r\n", "\n").replace("\r", "\n"))

    if variant.postprocess.dehyphenate:
        normalized = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", normalized)

    lines = [line.strip() for line in normalized.split("\n")]

    if variant.postprocess.dedupe_repeated_lines:
        lines = _dedupe_repeated_lines(lines)

    if variant.postprocess.strip_blank_lines:
        compacted: list[str] = []
        previous_blank = False
        for line in lines:
            is_blank = line == ""
            if is_blank and previous_blank:
                continue
            compacted.append(line)
            previous_blank = is_blank
        lines = compacted

    return "\n".join(lines).strip()


def _dedupe_repeated_lines(lines: list[str]) -> list[str]:
    deduped: list[str] = []
    previous_line = ""
    for line in lines:
        if line and line == previous_line:
            continue
        deduped.append(line)
        previous_line = line
    return deduped


def _build_doc_id(source_path: Path) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", source_path.stem).strip("-").lower()
    digest = _sha256_file(source_path)[:10]
    return f"{slug}-{digest}"


def _build_chunks(
    *,
    doc_id: str,
    pages: list[ParsedPage],
    variant: VariantConfig,
    page_extractors: dict[int, str],
) -> list[ParsedChunk]:
    chunks: list[ParsedChunk] = []

    for page in pages:
        page_chunks = _split_by_chars(
            text=page.canonical_text,
            target_chars=variant.chunking.target_chars,
            overlap_chars=variant.chunking.overlap_chars,
            min_chars=variant.chunking.min_chars,
        )
        for chunk_index, chunk_text in enumerate(page_chunks):
            if not chunk_text:
                continue
            chunks.append(
                ParsedChunk(
                    chunk_id=(f"{doc_id}-p{page.page_index + 1:04d}-c{chunk_index + 1:03d}"),
                    page_start=page.page_index,
                    page_end=page.page_index,
                    text=chunk_text,
                    type="passage",
                    meta={
                        "extractor": page_extractors.get(page.page_index, variant.extractor),
                    },
                )
            )
    return chunks


def _strip_repeated_margin_boilerplate(pages: list[ParsedPage]) -> None:
    if len(pages) < 2:
        return

    top_zone_lines = 2
    min_occurrences = max(2, int(len(pages) * 0.4 + 0.999))

    top_counts: dict[str, int] = {}

    for page in pages:
        lines = _non_empty_lines(page.canonical_text)
        top_zone = lines[:top_zone_lines]

        for signature in {_line_signature(line) for line in top_zone}:
            top_counts[signature] = top_counts.get(signature, 0) + 1

    top_boilerplate = {sig for sig, count in top_counts.items() if count >= min_occurrences}

    if not top_boilerplate:
        return

    for page in pages:
        lines = _non_empty_lines(page.canonical_text)
        if not lines:
            continue

        start = 0
        while start < len(lines) and start < top_zone_lines:
            if _line_signature(lines[start]) in top_boilerplate:
                start += 1
                continue
            break

        page.canonical_text = "\n".join(lines[start:]).strip()


def _split_by_chars(
    *,
    text: str,
    target_chars: int,
    overlap_chars: int,
    min_chars: int,
) -> list[str]:
    source = text.strip()
    if not source:
        return []

    if len(source) <= target_chars:
        return [source]

    if overlap_chars >= target_chars:
        overlap_chars = max(0, target_chars // 4)

    chunks: list[str] = []
    cursor = 0
    while cursor < len(source):
        end = min(len(source), cursor + target_chars)
        window = source[cursor:end].strip()
        if window:
            chunks.append(window)

        if end >= len(source):
            break

        next_cursor = end - overlap_chars
        if next_cursor <= cursor:
            next_cursor = end
        cursor = next_cursor

    if len(chunks) > 1 and len(chunks[-1]) < min_chars:
        merged = f"{chunks[-2]}\n{chunks[-1]}".strip()
        chunks[-2] = merged
        chunks.pop()

    return chunks


def _non_empty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.split("\n") if line.strip()]


def _line_signature(line: str) -> str:
    normalized = unicodedata.normalize("NFKC", line).lower()
    normalized = re.sub(r"\d+", "#", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _compute_metrics(*, parsed_document: ParsedDocument, elapsed_seconds: float) -> dict[str, Any]:
    non_empty_pages = sum(1 for page in parsed_document.pages if page.canonical_text.strip())
    non_empty_content_rate = non_empty_pages / max(1, parsed_document.page_count)

    lines: list[str] = []
    for page in parsed_document.pages:
        for line in page.canonical_text.split("\n"):
            cleaned = line.strip().lower()
            if len(cleaned) >= 8:
                lines.append(cleaned)

    line_counts: dict[str, int] = {}
    for line in lines:
        line_counts[line] = line_counts.get(line, 0) + 1

    duplicate_lines = sum(count - 1 for count in line_counts.values() if count > 1)
    duplicate_line_rate = duplicate_lines / max(1, len(lines))

    chunk_lengths = sorted(len(chunk.text) for chunk in parsed_document.chunks)
    chunk_p50 = _percentile(chunk_lengths, 50)
    chunk_p90 = _percentile(chunk_lengths, 90)

    return {
        "must_pass_gates": {
            "non_empty_content_rate": non_empty_content_rate,
            "duplicate_line_rate": duplicate_line_rate,
            "reliability": {
                "failure_rate": 0.0,
                "runtime_seconds": elapsed_seconds,
            },
        },
        "chunk_quality": {
            "chunk_count": len(parsed_document.chunks),
            "char_length_p50": chunk_p50,
            "char_length_p90": chunk_p90,
            "table_chunks": 0,
            "code_chunks": 0,
            "passage_chunks": len(parsed_document.chunks),
        },
    }


def _percentile(values: list[int], percentile: int) -> float:
    if not values:
        return 0.0

    if percentile <= 0:
        return float(values[0])
    if percentile >= 100:
        return float(values[-1])

    index = int(round(((len(values) - 1) * percentile) / 100))
    return float(values[index])


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _git_sha() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value if value else None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True)
    path.write_text(serialized + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, sort_keys=True) for row in rows]
    serialized = "\n".join(lines)
    if serialized:
        serialized += "\n"
    path.write_text(serialized, encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_chunks_markdown(
    *,
    path: Path,
    parsed_document: ParsedDocument,
    variant: VariantConfig,
) -> None:
    lines: list[str] = [
        f"# Chunk Review: {parsed_document.doc_id}",
        "",
        f"- Source: `{parsed_document.source_uri}`",
        f"- Variant: `{variant.variant_id}`",
        f"- Page count: {parsed_document.page_count}",
        f"- Chunk count: {len(parsed_document.chunks)}",
        "",
    ]

    for chunk in parsed_document.chunks:
        lines.extend(
            [
                f"## {chunk.chunk_id}",
                "",
                f"- Pages: {chunk.page_start + 1}-{chunk.page_end + 1}",
                f"- Type: {chunk.type}",
                f"- Extractor: {chunk.meta.get('extractor', variant.extractor)}",
                "",
                "```text",
                chunk.text,
                "```",
                "",
            ]
        )

    _write_text(path, "\n".join(lines))
