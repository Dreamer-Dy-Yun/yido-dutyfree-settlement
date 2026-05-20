###########################################
# Module name : router_tenant_edi_exports.py
# Module functions : Tenant EDI export and group APIs
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.05.20
# Note : Included by router_tenant_edi.py; do not duplicate the /api/tenant prefix here.
############################################

import datetime as _dt
import io
import json as _json
import urllib.parse as _urlparse

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select

from CUSTOMIZED.cust_deco_error import handle_http_error
from CUSTOMIZED.cust_logger import logger
from DATABASE import models
from DATABASE.dbms import DBManager
from PROCESSOR_DATA.edi_unified_export import EdiUnifiedExporter
from WEB_SERVER.auth.dependencies import get_current_user
from WEB_SERVER.routers.settings import get_db_manager
from WEB_SERVER.routers.tenant_helpers import (
    _get_current_tenant_schema_from_user,
    _get_current_tenant_schemas,
)

router = APIRouter()


def _parse_date(value: str) -> _dt.date:
    return _dt.datetime.strptime(value, "%Y.%m.%d").date()


def _validate_date_range(from_date: str, to_date: str) -> tuple[_dt.date, _dt.date]:
    d_from = _parse_date(from_date)
    d_to = _parse_date(to_date)
    if d_from > d_to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="from_date는 to_date보다 클 수 없습니다.")
    return d_from, d_to


def _normalize_sources(sources: str) -> list[str]:
    sources_norm = sources.strip().upper()
    src_list = ["SILLA", "LOTTE"] if sources_norm == "ALL" else [sources_norm]
    return [s for s in src_list if s in ("SILLA", "LOTTE")] or ["SILLA", "LOTTE"]


@router.get(
    "/data-mapping/edi-unified/export",
    summary="EDI 매핑 결과 엑셀 다운로드",
)
@handle_http_error
async def export_edi_unified_excel(
    from_date: str = Query(..., description="YYYY.MM.DD"),
    to_date: str = Query(..., description="YYYY.MM.DD"),
    sources: str = Query("all", description="all|silla|lotte"),
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    d_from, d_to = _validate_date_range(from_date, to_date)
    src_list = _normalize_sources(sources)

    tenant_schema = _get_current_tenant_schema_from_user(current_user)
    exporter = EdiUnifiedExporter(db=db, tenant_schema=tenant_schema, public_schema="public")
    df = await exporter.build_export_dataframe(
        sources=src_list,  # type: ignore[arg-type]
        from_date=d_from,
        to_date=d_to,
    )
    logger.info(
        "[EDI_UNIFIED][EXPORT] final df rows=%s empty=%s cols=%s sources=%s from=%s to=%s",
        0 if df is None else len(df),
        True if (df is None or getattr(df, "empty", True)) else False,
        [] if df is None else list(df.columns),
        src_list,
        d_from.strftime("%Y.%m.%d"),
        d_to.strftime("%Y.%m.%d"),
    )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # openpyxl/pandas가 다루기 어려운 object(리스트/딕셔너리 등)를 문자열로 정규화
        if df is None:
            df = pd.DataFrame()
        else:
            for col in df.columns:
                df[col] = df[col].map(
                    lambda v: _json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                )
        try:
            df.to_excel(writer, index=False, sheet_name="EDI매핑결과")
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"엑셀 생성 실패: {str(e)}")
    output.seek(0)

    filename_ascii = f"EDI_mapping_result_({d_from.strftime('%Y.%m.%d')}~{d_to.strftime('%Y.%m.%d')}).xlsx"
    filename_utf8_quoted = _urlparse.quote(filename_ascii, safe="")
    headers = {
        "Content-Disposition": (
            f"attachment; filename=\"{filename_ascii}\"; filename*=UTF-8''{filename_utf8_quoted}"
        )
    }
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get(
    "/data-mapping/edi-unified/groups",
    summary="EDI_UNIFIED 그룹(면세점+영수증번호) 목록 조회",
)
@handle_http_error
async def list_edi_unified_groups(
    from_date: str = Query(..., description="YYYY.MM.DD"),
    to_date: str = Query(..., description="YYYY.MM.DD"),
    sources: str = Query("all", description="all|silla|lotte"),
    status_filter: str = Query("all", description="all|full|partial|unmapped"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    d_from, d_to = _validate_date_range(from_date, to_date)
    src_list = _normalize_sources(sources)

    sf = status_filter.strip().lower()
    if sf not in ("all", "full", "partial", "unmapped"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="status_filter는 all|full|partial|unmapped 만 가능합니다.")

    schemas = _get_current_tenant_schemas(current_user)
    base = (
        select(
            models.EDI_Unified.dutyfree_operator.label("dutyfree_operator"),
            models.EDI_Unified.receipt_no.label("receipt_no"),
            func.max(models.EDI_Unified.datetime_purchase).label("datetime_purchase_max"),
            func.count().label("line_count"),
            func.max(models.VerifiedPassport.name).label("customer_name_any"),
            func.max(models.EDI_Unified.uuid_receipt).label("uuid_receipt_any"),
            func.max(models.EDI_Unified.uuid_passport).label("uuid_passport_any"),
        )
        .select_from(models.EDI_Unified)
        .outerjoin(
            models.VerifiedPassport,
            models.EDI_Unified.uuid_passport == models.VerifiedPassport.uuid_record,
        )
        .where(
            models.EDI_Unified.dutyfree_operator.in_(src_list),
            models.EDI_Unified.datetime_purchase.is_not(None),
            models.EDI_Unified.datetime_purchase >= d_from,
            models.EDI_Unified.datetime_purchase <= d_to,
        )
    )

    if sf == "full":
        base = base.where(
            models.EDI_Unified.uuid_receipt.is_not(None),
            models.EDI_Unified.uuid_passport.is_not(None),
        )
    elif sf == "partial":
        base = base.where(
            models.EDI_Unified.uuid_receipt.is_not(None),
            models.EDI_Unified.uuid_passport.is_(None),
        )
    elif sf == "unmapped":
        base = base.where(models.EDI_Unified.uuid_receipt.is_(None))

    base = base.group_by(models.EDI_Unified.dutyfree_operator, models.EDI_Unified.receipt_no)
    total = int((await db.execute_query(select(func.count()).select_from(base.subquery()), schemas=schemas)).scalar() or 0)

    offset = (page - 1) * page_size
    stmt = base.order_by(func.max(models.EDI_Unified.datetime_purchase).desc()).offset(offset).limit(page_size)
    result = await db.execute_query(stmt, schemas=schemas)
    rows = result.mappings().all()

    return {
        "items": [
            {
                "dutyfree_operator": r.get("dutyfree_operator"),
                "receipt_no": r.get("receipt_no"),
                "datetime_purchase": r.get("datetime_purchase_max"),
                "line_count": int(r.get("line_count") or 0),
                "customer_name": r.get("customer_name_any"),
                "uuid_receipt": r.get("uuid_receipt_any"),
                "uuid_passport": r.get("uuid_passport_any"),
            }
            for r in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get(
    "/data-mapping/edi-unified/groups/detail",
    summary="EDI_UNIFIED 그룹 상세(라인) 조회",
)
@handle_http_error
async def get_edi_unified_group_detail(
    dutyfree_operator: str = Query(...),
    receipt_no: str = Query(...),
    from_date: str = Query(..., description="YYYY.MM.DD"),
    to_date: str = Query(..., description="YYYY.MM.DD"),
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    d_from, d_to = _validate_date_range(from_date, to_date)
    op = dutyfree_operator.strip().upper()
    if not op:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="dutyfree_operator가 필요합니다.")
    rn = receipt_no.strip()
    if not rn:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="receipt_no가 필요합니다.")

    schemas = _get_current_tenant_schemas(current_user)
    stmt = (
        select(models.EDI_Unified)
        .where(
            models.EDI_Unified.dutyfree_operator == op,
            models.EDI_Unified.receipt_no == rn,
            models.EDI_Unified.datetime_purchase.is_not(None),
            models.EDI_Unified.datetime_purchase >= d_from,
            models.EDI_Unified.datetime_purchase <= d_to,
        )
        .order_by(models.EDI_Unified.product_code.asc())
    )

    result = await db.execute_query(stmt, schemas=schemas)
    rows = result.scalars().all()

    items = []
    for row in rows:
        data = {c.name: getattr(row, c.name) for c in row.__table__.columns}
        data.pop("id", None)
        items.append(data)

    return {"items": items, "count": len(items), "dutyfree_operator": op, "receipt_no": rn}
