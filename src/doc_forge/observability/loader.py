"""Filesystem ingester for central eval/log observability metadata."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

import sqlalchemy as sa
from dotenv import load_dotenv

from doc_forge.evaluation.answer_layer import AnswerLayerRunResult
from doc_forge.query import QueryContextManifest

from .persistence import (
    EvalCaseResultRecord,
    LogSourceRecord,
    ObservabilityStore,
    QueryContextAssetRecord,
    QueryContextRunRecord,
)

ModelT = TypeVar("ModelT")


@dataclass(frozen=True)
class EvalOpsScanStats:
    scanned_bundles: int
    indexed_bundles: int


class EvalOpsLoader:
    """Indexes collected query bundles into the observability metadata store."""

    def __init__(
        self,
        *,
        store: ObservabilityStore,
        context_root: Path,
        repo_root: Path | None = None,
    ) -> None:
        self._store = store
        self._context_root = context_root.resolve()
        self._repo_root = (repo_root or _repo_root()).resolve()

    @classmethod
    def from_database_url(
        cls,
        *,
        database_url: str | None = None,
        context_root: Path | None = None,
        repo_root: Path | None = None,
    ) -> EvalOpsLoader:
        load_dotenv()
        root = (repo_root or _repo_root()).resolve()
        resolved_context_root = (context_root or root / "data" / "context" / "queries").resolve()
        engine = sa.create_engine(database_url or _resolve_database_url())
        return cls(
            store=ObservabilityStore(engine),
            context_root=resolved_context_root,
            repo_root=root,
        )

    def create_schema(self) -> None:
        self._store.create_schema()

    def scan_once(self) -> EvalOpsScanStats:
        self.create_schema()
        scanned = 0
        indexed = 0
        for manifest_path in sorted(self._context_root.glob("*/manifest.json")):
            scanned += 1
            self._index_bundle(manifest_path.parent)
            indexed += 1
        return EvalOpsScanStats(scanned_bundles=scanned, indexed_bundles=indexed)

    def scan_forever(self, *, interval_seconds: float) -> None:
        while True:
            self.scan_once()
            time.sleep(interval_seconds)

    def _index_bundle(self, bundle_root: Path) -> None:
        manifest = QueryContextManifest.model_validate_json(
            (bundle_root / "manifest.json").read_text(encoding="utf-8")
        )
        eval_result = _load_optional_model(bundle_root / "eval-result.json", AnswerLayerRunResult)

        self._store.replace_query_context(
            run_record=_manifest_to_run_record(
                manifest=manifest,
                bundle_root=_display_path(bundle_root, self._repo_root),
            ),
            asset_records=_asset_records_for_manifest(manifest),
            log_records=_log_records_for_manifest(manifest),
            eval_record=_eval_record_for_manifest(manifest, eval_result),
        )


def _manifest_to_run_record(
    *,
    manifest: QueryContextManifest,
    bundle_root: str,
) -> QueryContextRunRecord:
    return QueryContextRunRecord(
        query_id=manifest.query_id,
        workspace_id=manifest.workspace_id,
        question=manifest.question,
        submitted_at=manifest.submitted_at,
        completed_at=manifest.completed_at,
        collected_at=manifest.collected_at,
        source_kind=manifest.source_kind.value,
        run_id=manifest.run_id,
        test_id=manifest.test_id,
        case_id=manifest.case_id,
        support_state=manifest.support_state,
        answer_mode=manifest.answer_mode,
        evaluator_outcome=manifest.evaluator_outcome,
        bundle_root=bundle_root,
        environment=manifest.environment,
    )


def _asset_records_for_manifest(manifest: QueryContextManifest) -> list[QueryContextAssetRecord]:
    records: list[QueryContextAssetRecord] = []
    assets_payload = manifest.assets.model_dump()
    missing_assets = set(manifest.missing_assets)
    for asset_kind, relative_path in sorted(assets_payload.items()):
        if relative_path is not None:
            records.append(
                QueryContextAssetRecord(
                    query_id=manifest.query_id,
                    asset_kind=asset_kind,
                    relative_path=relative_path,
                    present=True,
                    missing_reason=None,
                )
            )
            continue
        records.append(
            QueryContextAssetRecord(
                query_id=manifest.query_id,
                asset_kind=asset_kind,
                relative_path=None,
                present=False,
                missing_reason="manifest_missing" if asset_kind in missing_assets else None,
            )
        )
    for asset_kind in sorted(missing_assets - set(assets_payload)):
        records.append(
            QueryContextAssetRecord(
                query_id=manifest.query_id,
                asset_kind=asset_kind,
                relative_path=None,
                present=False,
                missing_reason="manifest_missing",
            )
        )
    for log_asset in manifest.log_assets:
        bundle_kind = f"{log_asset.service}_log"
        records.append(
            QueryContextAssetRecord(
                query_id=manifest.query_id,
                asset_kind=bundle_kind,
                relative_path=log_asset.bundle_path,
                present=log_asset.bundle_path is not None,
                missing_reason=None if log_asset.bundle_path is not None else "bundle_path_missing",
            )
        )
    return records


def _log_records_for_manifest(manifest: QueryContextManifest) -> list[LogSourceRecord]:
    return [
        LogSourceRecord(
            query_id=manifest.query_id,
            service=log_asset.service,
            source_path=log_asset.source_path,
            matched_line_count=log_asset.matched_line_count,
        )
        for log_asset in manifest.log_assets
    ]


def _eval_record_for_manifest(
    manifest: QueryContextManifest,
    eval_result: AnswerLayerRunResult | None,
) -> EvalCaseResultRecord | None:
    if eval_result is None or manifest.case_id is None:
        return None
    return EvalCaseResultRecord(
        query_id=manifest.query_id,
        case_id=manifest.case_id,
        workspace_id=manifest.workspace_id,
        run_id=manifest.run_id,
        test_id=manifest.test_id,
        trust_outcome=eval_result.overall_trust_outcome.value,
        support_alignment_verdict=eval_result.support_alignment.verdict.value,
        scope_control_verdict=eval_result.scope_control.verdict.value,
        provenance_quality_verdict=eval_result.provenance_quality.verdict.value,
        abstention_behavior_verdict=eval_result.abstention_behavior.verdict.value,
        overall_trust_verdict=eval_result.overall_trust_result.verdict.value,
    )


def _load_optional_model(path: Path, model_cls: type[ModelT]) -> ModelT | None:
    if not path.exists():
        return None
    return model_cls.model_validate_json(path.read_text(encoding="utf-8"))  # type: ignore[attr-defined,no-any-return]


def _resolve_database_url() -> str:
    value = os.environ.get("DOC_FORGE_OBSERVABILITY_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not value:
        raise RuntimeError(
            "DOC_FORGE_OBSERVABILITY_DATABASE_URL or DATABASE_URL is required "
            "for observability loading"
        )
    return value


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return str(path.resolve())
