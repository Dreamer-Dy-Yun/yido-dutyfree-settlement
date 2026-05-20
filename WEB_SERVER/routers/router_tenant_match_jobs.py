###########################################
# Module name : router_tenant_match_jobs.py
# Module functions : Tenant match queue and status routes
# Written by : Codex
# Created at : 2026.05.20
# Note : Included by router_tenant_matching.py; do not duplicate /api/tenant prefix here.
############################################

import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import and_, func, select

from CUSTOMIZED.cust_deco_error import handle_http_error
from DATABASE import models
from DATABASE.dbms import DBManager
from PROCESSOR_MATCHING.matcher_registry import dict_matcher
from WEB_SERVER.auth.dependencies import get_current_user
from WEB_SERVER.routers.settings import get_db_manager
from WEB_SERVER.routers.tenant_helpers import (
    _get_current_tenant_schema_from_user,
    _get_current_tenant_schemas,
)
from WEB_SERVER.routers.tenant_schemas import MatchJobRequest
from WEB_SERVER.services.service_match_queue import enqueue_match_job

router = APIRouter()


@router.post(
    "/data-mapping/match-attempt",
    summary="Request tenant receipt/passport matching job",
)
@handle_http_error
async def request_match_attempt(
    try_fallback: bool = Form(True, description="Run fallback matching when available"),
    current_user: models.User = Depends(get_current_user),
):
    tenant_schema = _get_current_tenant_schema_from_user(current_user)
    job = enqueue_match_job(
        tenant_schema=tenant_schema,
        requested_by=getattr(current_user, "id", None),
        try_fallback=try_fallback,
    )
    return {"message": "매칭 작업이 큐에 등록되었습니다.", "job": job}


@router.post(
    "/internal/match/run",
    summary="Run internal tenant matching job",
)
@handle_http_error
async def internal_run_match_job(
    payload: MatchJobRequest,
    db: DBManager = Depends(get_db_manager),
):
    matcher_key = str(payload.matcher_key or "LOTTE").upper()
    matcher_cls = dict_matcher.get(matcher_key)
    if matcher_cls is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 matcher_key 입니다: {matcher_key}",
        )

    matcher = matcher_cls(
        db=db,
        public_schema="public",
        tenant_schema=payload.tenant_schema,
    )
    await matcher.run(locked_by=uuid.uuid4().hex, try_fallback=payload.try_fallback)
    return {
        "message": "매칭 작업이 완료되었습니다.",
        "tenant_schema": payload.tenant_schema,
        "matcher_key": matcher_key,
    }


@router.get(
    "/data-mapping/match-status",
    summary="Get tenant matching status",
)
@handle_http_error
async def get_match_status(
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    total_stmt = select(func.count(models.VerifiedReceipt.id)).where(
        models.VerifiedReceipt.is_verified.is_(True)
    )
    unmatched_stmt = select(func.count(models.VerifiedReceipt.id)).where(
        and_(
            models.VerifiedReceipt.is_verified.is_(True),
            models.VerifiedReceipt.is_processed.is_(False),
        )
    )
    total_count = (await db.execute_query(total_stmt, schemas=schemas)).scalar() or 0
    unmatched_count = (await db.execute_query(unmatched_stmt, schemas=schemas)).scalar() or 0
    matched_count = max(int(total_count) - int(unmatched_count), 0)
    return {
        "total_count": int(total_count),
        "matched_count": matched_count,
        "unmatched_count": int(unmatched_count),
    }
