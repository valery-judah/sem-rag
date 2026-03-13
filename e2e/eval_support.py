from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from doc_forge.evaluation import (
    AnswerLayerCaseRepository,
    AnswerLayerCitation,
    AnswerLayerEvaluator,
    AnswerLayerRunInput,
    AnswerLayerRunResult,
)
from doc_forge.query import (
    QueryContextCollectionExtras,
    QueryContextCollector,
    QueryContextSourceKind,
)
from doc_forge.query.review import QueryCitationReview, QueryRunReviewSummary, QueryTraceReview
from e2e.query_support import ExecutedQueryRun, execute_query_run
from e2e.support import SystemDriver

REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_CORPUS_DIR = REPO_ROOT / "evals" / "corpus"
SMOKE_CASE_IDS = (
    "lookup_rn1_001",
    "psynth_rn2_001",
    "unsup_rn2_001",
    "uqt_rn2_007",
    "conflict_rn2_001",
    "istruct_rn3_006",
)


@dataclass(frozen=True)
class UploadedCorpusDocument:
    corpus_id: str
    runtime_doc_id: str


@dataclass(frozen=True)
class ExecutedEvalCase:
    case_id: str
    workspace_id: str
    query_id: str
    answer_text: str
    citations: list[AnswerLayerCitation]
    summary_payload: QueryRunReviewSummary
    citations_payload: QueryCitationReview
    trace_payload: QueryTraceReview
    query_response: ExecutedQueryRun
    evaluation_result: AnswerLayerRunResult
    uploaded_documents: list[UploadedCorpusDocument]
    context_bundle_root: Path | None = None


class EvalCaseExecutor:
    def __init__(
        self,
        *,
        repository: AnswerLayerCaseRepository | None = None,
        evaluator: AnswerLayerEvaluator | None = None,
    ) -> None:
        self._repository = repository or AnswerLayerCaseRepository.from_repo_root(REPO_ROOT)
        self._evaluator = evaluator or AnswerLayerEvaluator(self._repository)

    @property
    def repository(self) -> AnswerLayerCaseRepository:
        return self._repository

    def execute_case(self, *, driver: SystemDriver, case_id: str) -> ExecutedEvalCase:
        case_spec = self._repository.get(case_id)
        workspace_id = f"ws-eval-{case_id}"
        uploaded_documents = self._upload_case_corpus(
            driver=driver,
            case_id=case_id,
            corpus_id=case_spec.case.corpus_id,
            workspace_id=workspace_id,
        )
        runtime_doc_map = {item.runtime_doc_id: item.corpus_id for item in uploaded_documents}
        executed_query = execute_query_run(
            driver=driver,
            workspace_id=workspace_id,
            question=case_spec.case.question_spec.question,
        )
        run_input = runtime_query_to_answer_layer_input(
            case_id=case_id,
            query_run=executed_query,
            runtime_doc_id_map=runtime_doc_map,
        )
        evaluation_result = self._evaluator.evaluate(run_input)
        context_bundle_root = _collect_query_context_bundle(
            driver=driver,
            case_id=case_id,
            executed_query=executed_query,
            evaluation_result=evaluation_result,
            uploaded_documents=uploaded_documents,
        )
        executed_case = ExecutedEvalCase(
            case_id=case_id,
            workspace_id=workspace_id,
            query_id=executed_query.query_id,
            answer_text=run_input.answer_text,
            citations=run_input.citations,
            summary_payload=executed_query.summary,
            citations_payload=executed_query.citations_review,
            trace_payload=executed_query.trace,
            query_response=executed_query,
            evaluation_result=evaluation_result,
            uploaded_documents=uploaded_documents,
            context_bundle_root=context_bundle_root,
        )
        _write_case_debug_artifacts(driver=driver, executed_case=executed_case)
        return executed_case

    def _upload_case_corpus(
        self,
        *,
        driver: SystemDriver,
        case_id: str,
        corpus_id: str,
        workspace_id: str,
    ) -> list[UploadedCorpusDocument]:
        corpus_path = corpus_path_for_id(corpus_id)
        title = _title_for_corpus_id(corpus_id)
        uploaded = driver.ingest_document(
            path=corpus_path.relative_to(REPO_ROOT),
            title=title,
            workspace_id=workspace_id,
        )
        driver.stack.log(
            "authored eval corpus uploaded",
            case_id=case_id,
            corpus_id=corpus_id,
            runtime_doc_id=uploaded.doc_id,
        )
        return [UploadedCorpusDocument(corpus_id=corpus_id, runtime_doc_id=uploaded.doc_id)]


def corpus_path_for_id(corpus_id: str) -> Path:
    markdown_path = EVAL_CORPUS_DIR / f"{corpus_id}.md"
    pdf_path = EVAL_CORPUS_DIR / f"{corpus_id}.pdf"
    if markdown_path.exists():
        return markdown_path
    if pdf_path.exists():
        return pdf_path
    raise FileNotFoundError(f"no committed eval corpus found for {corpus_id!r}")


def runtime_query_to_answer_layer_input(
    *,
    case_id: str,
    query_run: ExecutedQueryRun,
    runtime_doc_id_map: dict[str, str],
) -> AnswerLayerRunInput:
    citations = [
        _source_reference_to_answer_layer_citation(citation.source_reference, runtime_doc_id_map)
        for citation in query_run.response.citations.citations
    ]
    return AnswerLayerRunInput(
        case_id=case_id,
        answer_text=query_run.response.answer.answer_text,
        citations=citations,
    )


def _source_reference_to_answer_layer_citation(
    source_reference: Any,
    runtime_doc_id_map: dict[str, str],
) -> AnswerLayerCitation:
    authored_doc_id = runtime_doc_id_map.get(source_reference.doc_id, source_reference.doc_id)
    page_start, page_end = _parse_page_label(source_reference.page_label)
    return AnswerLayerCitation(
        doc_id=authored_doc_id,
        document_title=source_reference.document_title,
        section_path=list(source_reference.heading_path or []) or None,
        page_start=page_start,
        page_end=page_end,
        section_anchor=source_reference.passage_anchor,
    )


def _parse_page_label(page_label: str | None) -> tuple[int | None, int | None]:
    if page_label is None:
        return None, None
    single = re.fullmatch(r"p\.\s*(\d+)", page_label)
    if single is not None:
        return int(single.group(1)), None
    page_range = re.fullmatch(r"pp\.\s*(\d+)-(\d+)", page_label)
    if page_range is not None:
        return int(page_range.group(1)), int(page_range.group(2))
    return None, None


def _title_for_corpus_id(corpus_id: str) -> str:
    return corpus_id.replace("-", " ").title()


def _write_case_debug_artifacts(*, driver: SystemDriver, executed_case: ExecutedEvalCase) -> None:
    artifact_dir = driver.stack.artifact_root / "eval-query-runs" / executed_case.case_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        "query-response.json": executed_case.query_response.response.model_dump(mode="json"),
        "query-summary.json": executed_case.summary_payload.model_dump(mode="json"),
        "query-citations.json": executed_case.citations_payload.model_dump(mode="json"),
        "query-trace.json": executed_case.trace_payload.model_dump(mode="json"),
        "evaluator-result.json": executed_case.evaluation_result.model_dump(mode="json"),
        "execution-metadata.json": {
            "case_id": executed_case.case_id,
            "workspace_id": executed_case.workspace_id,
            "query_id": executed_case.query_id,
            "uploaded_documents": [
                {
                    "corpus_id": item.corpus_id,
                    "runtime_doc_id": item.runtime_doc_id,
                }
                for item in executed_case.uploaded_documents
            ],
        },
    }
    for filename, payload in payloads.items():
        path = artifact_dir / filename
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        driver.stack.record_query_debug_artifact(
            path.relative_to(driver.stack.artifact_root).as_posix()
        )
    if executed_case.context_bundle_root is not None:
        driver.stack.record_query_context_artifact(
            executed_case.context_bundle_root.relative_to(REPO_ROOT).as_posix()
        )


def _collect_query_context_bundle(
    *,
    driver: SystemDriver,
    case_id: str,
    executed_query: ExecutedQueryRun,
    evaluation_result: AnswerLayerRunResult,
    uploaded_documents: list[UploadedCorpusDocument],
) -> Path | None:
    if driver.stack.current_test_id is not None:
        driver.stack.archive_scenario_logs(test_id=driver.stack.current_test_id)
    extras = QueryContextCollectionExtras(
        source_kind=QueryContextSourceKind.EVAL,
        case_id=case_id,
        test_id=driver.stack.current_test_id,
        query_response_payload=executed_query.response.model_dump(mode="json"),
        eval_result_payload=evaluation_result.model_dump(mode="json"),
        execution_metadata_payload={
            "case_id": case_id,
            "workspace_id": executed_query.workspace_id,
            "query_id": executed_query.query_id,
            "uploaded_documents": [
                {
                    "corpus_id": item.corpus_id,
                    "runtime_doc_id": item.runtime_doc_id,
                }
                for item in uploaded_documents
            ],
        },
    )
    collector = QueryContextCollector.from_database_url(
        database_url=driver.stack.database_url,
        repo_root=REPO_ROOT,
    )
    result = collector.collect(executed_query.query_id, extras=extras)
    return result.bundle_root
