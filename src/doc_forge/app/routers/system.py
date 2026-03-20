# ruff: noqa: B008
# pyright: reportUnusedFunction=false
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from doc_forge.app.services.system import SystemAppService

from ..api_examples import HEALTHZ_ENDPOINT_DESCRIPTION, READYZ_ENDPOINT_DESCRIPTION
from ..deps import get_system_app_service
from ..schemas import ErrorResponse, SystemStatusResponse

router = APIRouter(tags=["System"])


@router.get(
    "/healthz",
    response_model=SystemStatusResponse,
    summary="Health Check",
    description=HEALTHZ_ENDPOINT_DESCRIPTION,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)
def healthz(
    service: Annotated[SystemAppService, Depends(get_system_app_service)],
) -> SystemStatusResponse:
    return service.get_health()


@router.get(
    "/readyz",
    response_model=SystemStatusResponse,
    summary="Readiness Check",
    description=READYZ_ENDPOINT_DESCRIPTION,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Readiness check failed due to unreachable dependencies",
        },
    },
)
def readyz(
    service: Annotated[SystemAppService, Depends(get_system_app_service)],
) -> SystemStatusResponse:
    return service.get_readiness()
