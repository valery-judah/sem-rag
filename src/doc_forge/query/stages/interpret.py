"""Stage-2 query interpretation stage."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from doc_forge.query.contracts import CorpusSnapshot, QueryRequest, QueryStageName
from doc_forge.query.interpretation import QueryInterpretationResult, QueryInterpreter
from doc_forge.query.trace import QueryStageTrace, QueryStageTraceStatus, utc_now

STAGE_NAME = QueryStageName.INTERPRET


class InterpretationStageResult(BaseModel):
    """Structured result of the interpretation stage."""

    model_config = ConfigDict(extra="forbid")

    interpretation: QueryInterpretationResult
    trace: QueryStageTrace


def run(
    *,
    query_id: str,
    request: QueryRequest,
    snapshot: CorpusSnapshot,
    interpreter: QueryInterpreter,
) -> InterpretationStageResult:
    """Interpret a query and return its persisted stage-trace payload."""

    started_at = utc_now()
    interpretation = interpreter.interpret(
        request=request,
        snapshot=snapshot,
    )
    finished_at = utc_now()
    trace = QueryStageTrace(
        query_id=query_id,
        stage_name=STAGE_NAME,
        stage_status=QueryStageTraceStatus.SUCCEEDED,
        started_at=started_at,
        finished_at=finished_at,
        payload={
            "interpreted_query": interpretation.interpreted_query.model_dump(mode="json"),
            "interpreter": interpretation.metadata.model_dump(mode="json"),
        },
    )
    return InterpretationStageResult(
        interpretation=interpretation,
        trace=trace,
    )
