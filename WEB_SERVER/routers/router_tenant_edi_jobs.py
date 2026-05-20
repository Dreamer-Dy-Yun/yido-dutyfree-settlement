###########################################
# Module name : router_tenant_edi_jobs.py
# Module functions : Tenant EDI upload and unified job APIs
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.05.20
# Note : Included by router_tenant_edi.py; do not duplicate the /api/tenant prefix here.
############################################

import io
import time

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from CUSTOMIZED.cust_deco_error import handle_http_error
from CUSTOMIZED.cust_logger import logger
from DATABASE import models
from DATABASE.dbms import DBManager
from PROCESSOR_DATA.edi_unified_service import EdiUnifiedService
from PROCESSOR_DATA.parsers.edi_lotte import EdiLotte
from PROCESSOR_DATA.parsers.edi_silla import EdiSilla
from PROCESSOR_DATA.patch import fix_invalid_datetime_in_xlsx_bytes
from WEB_SERVER.auth.dependencies import get_current_user
from WEB_SERVER.routers.settings import get_db_manager
from WEB_SERVER.routers.tenant_helpers import (
    _get_current_tenant_schema_from_user,
    _get_current_tenant_schemas,
)
from WEB_SERVER.routers.tenant_schemas import (
    EdiUnifiedJobEnqueueRequest,
    EdiUnifiedJobRequest,
)
from WEB_SERVER.services.service_edi_unified_queue import (
    enqueue_edi_unified_job,
    get_edi_unified_job_status,
)

router = APIRouter()


@router.post(
    "/data-mapping/edi-upload",
    summary="EDI 데이터 업로드",
    description="면세점(롯데/신라) 구분과 엑셀 파일을 받아 파서로 파싱 후 해당 테이블에 업서트합니다.",
)
@handle_http_error
async def upload_edi_data(
    file: UploadFile = File(..., description="EDI/엑셀 파일"),
    edi_source: str = Form(..., description="면세점 구분: lotte | silla"),
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    """
    EDI/엑셀 파일 업로드 -> PROCESSOR_DATA 파서로 파싱 -> 테넌트 스키마 EDI 테이블에 업서트.
    """
    filename = file.filename or ""
    edi_source_lower = edi_source.strip().lower()
    if edi_source_lower not in ("lotte", "silla"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="edi_source는 lotte 또는 silla만 가능합니다.",
        )
    if not filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="EDI 업로드는 엑셀(.xlsx, .xls)만 지원합니다.",
        )

    t0 = time.perf_counter()
    contents = await file.read()
    # 일부 엑셀에서 날짜 문자열이 "YYYYMMDDTHHMMSS" 형태로 들어오면 openpyxl이 파싱 중 예외를 낸다.
    # 소스(롯데/신라)와 무관하게 xlsx 인 경우에는 사전 패치로 안전하게 처리한다.
    if filename.lower().endswith(".xlsx"):
        try:
            contents = fix_invalid_datetime_in_xlsx_bytes(contents)
        except Exception:
            # 패치 실패 시에도 원본으로 파싱을 시도한다.
            pass

    # EDI 파서가 엑셀 로딩/플랫헤더/타입 변환을 모두 담당하도록 위임
    try:
        buffer = io.BytesIO(contents)
        if edi_source_lower == "lotte":
            parser = EdiLotte()
            table = models.EdiLotte
        elif edi_source_lower == "silla":
            parser = EdiSilla()
            table = models.EdiSilla
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="지원하지 않는 데이터 소스입니다.")

        df_parsed = parser.set_data(buffer).parse()
        t1 = time.perf_counter()
    except HTTPException:
        # 위에서 명시적으로 만든 HTTPException은 그대로 전달
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="엑셀을 읽는 중 오류가 발생했습니다.",
        )

    if df_parsed.empty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="파싱 결과가 비어 있습니다.")

    try:
        upsert_result = await db.upsert_batch(table=table, data=df_parsed, schemas=schemas)
        rows_upserted = int(upsert_result["cnt_success_rows"])
        t2 = time.perf_counter()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="저장에 실패했습니다.",
        )

    parse_sec = round(t1 - t0, 2)
    db_sec = round(t2 - t1, 2)
    logger.info("EDI upload: parse=%ss, db=%ss, rows=%s", parse_sec, db_sec, rows_upserted)

    return {
        "message": "파일이 업로드되어 반영되었습니다.",
        "filename": filename,
        "edi_source": edi_source_lower,
        "rows_upserted": rows_upserted,
    }


@router.post(
    "/data-mapping/edi-unified/run",
    summary="EDI_UNIFIED 동기화/매핑 작업 요청",
    description="현재 테넌트에 대해 EDI_UNIFIED 동기화/매핑 작업을 Redis 큐에 등록합니다.",
)
@handle_http_error
async def request_edi_unified_run(
    payload: EdiUnifiedJobEnqueueRequest,
    current_user: models.User = Depends(get_current_user),
):
    tenant_schema = _get_current_tenant_schema_from_user(current_user)
    sources = [s.strip().upper() for s in (payload.sources or [])]
    sources = [s for s in sources if s in ("SILLA", "LOTTE")] or ["SILLA", "LOTTE"]

    logger.info(
        "[EDI_UNIFIED][ENQUEUE] request_edi_unified_run | tenant_schema=%s user_id=%s sources=%s",
        tenant_schema,
        getattr(current_user, "id", None),
        sources,
    )

    job = enqueue_edi_unified_job(
        tenant_schema=tenant_schema,
        requested_by=getattr(current_user, "id", None),
        sources=sources,  # type: ignore[arg-type]
        max_rows=None,
        fill_receipt=True,
        fill_passport=True,
    )

    logger.info(
        "[EDI_UNIFIED][ENQUEUE] job_enqueued | job_id=%s status=%s tenant_schema=%s sources=%s",
        job.get("job_id"),
        "queued",
        tenant_schema,
        sources,
    )

    return {"message": "EDI 매핑 작업이 큐에 등록되었습니다.", "job": job}


@router.get(
    "/data-mapping/edi-unified/job/{job_id}",
    summary="EDI_UNIFIED 작업 상태 조회",
)
@handle_http_error
async def get_edi_unified_job(job_id: str):
    status_data = get_edi_unified_job_status(job_id)
    if not status_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job_id를 찾을 수 없습니다.")
    return {"job": status_data}


@router.post(
    "/internal/edi-unified/run",
    summary="내부용 EDI_UNIFIED 작업 실행",
    description="EDI_UNIFIED 워커가 호출하는 내부 전용 엔드포인트로, 지정된 테넌트에 대해 EDI_UNIFIED 로직을 실행합니다.",
)
@handle_http_error
async def internal_run_edi_unified_job(
    payload: EdiUnifiedJobRequest,
    db: DBManager = Depends(get_db_manager),
):
    sources = [s.strip().upper() for s in (payload.sources or [])]
    sources = [s for s in sources if s in ("SILLA", "LOTTE")] or ["SILLA", "LOTTE"]

    svc = EdiUnifiedService(db=db, tenant_schema=payload.tenant_schema, public_schema="public")

    import time as _time

    t0 = _time.perf_counter()
    logger.info(
        "[EDI_UNIFIED][WORKER] internal_run_edi_unified_job start | "
        "tenant_schema=%s sources=%s max_rows=%s fill_receipt=%s fill_passport=%s",
        payload.tenant_schema,
        sources,
        payload.max_rows,
        payload.fill_receipt,
        payload.fill_passport,
    )

    await svc.run(
        sources=sources,  # type: ignore[arg-type]
        max_rows=payload.max_rows,
        fill_receipt=bool(payload.fill_receipt),
        fill_passport=bool(payload.fill_passport),
    )

    elapsed = round(_time.perf_counter() - t0, 3)
    logger.info(
        "[EDI_UNIFIED][WORKER] internal_run_edi_unified_job done | tenant_schema=%s total=%.3fs",
        payload.tenant_schema,
        elapsed,
    )

    return {"message": "EDI_UNIFIED 작업이 완료되었습니다.", "tenant_schema": payload.tenant_schema, "sources": sources}
