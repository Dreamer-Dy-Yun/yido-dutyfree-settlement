###########################################
# Module name : router_tenant_match_results.py
# Module functions : Tenant match results and review-list routes
# Written by : Codex
# Created at : 2026.05.20
# Note : Included by router_tenant_matching.py; do not duplicate /api/tenant prefix here.
############################################

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from CUSTOMIZED.cust_deco_error import handle_http_error
from DATABASE import models
from DATABASE.dbms import DBManager
from DATABASE.models.tenant_model import Matched
from WEB_SERVER.auth.dependencies import get_current_user
from WEB_SERVER.routers.settings import get_db_manager
from WEB_SERVER.routers.tenant_helpers import _get_current_tenant_schemas

router = APIRouter()


def _image(row: dict[str, Any]) -> dict[str, Any]:
    coord = row.get("coordinate_verified") or row.get("coordinate_ocr") or {}
    return {
        "hash_img": row.get("hash_img"),
        "path": row.get("image_path"),
        "coordinate": {
            "top": coord.get("top", 0),
            "bottom": coord.get("bottom", 0),
            "left": coord.get("left", 0),
            "right": coord.get("right", 0),
        }
        if isinstance(coord, dict)
        else None,
    }


def _passport_candidate_select():
    return (
        select(
            models.VerifiedPassport.uuid_record.label("uuid_record"),
            models.VerifiedPassport.country_code,
            models.VerifiedPassport.passport_no,
            models.VerifiedPassport.name,
            models.VerifiedPassport.coordinate,
            models.VerifiedPassport.hash_img,
            models.Image.path.label("image_path"),
        )
        .select_from(models.VerifiedPassport)
        .join(models.Image, models.Image.hash == models.VerifiedPassport.hash_img, isouter=True)
    )


@router.get("/data-mapping/matches", summary="List tenant match results")
@handle_http_error
async def list_matches(
    status_filter: str = Query("all", alias="status", description="'all' | 'matched' | 'unmatched'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    base_stmt = (
        select(
            Matched.uuid_receipt.label("uuid_receipt"),
            Matched.uuid_passport.label("uuid_passport"),
            models.VerifiedReceipt.dutyfree_company.label("dutyfree_company"),
            models.VerifiedReceipt.receipt_no.label("receipt_no"),
            models.VerifiedReceipt.name.label("name"),
        )
        .select_from(Matched)
        .join(models.VerifiedReceipt, models.VerifiedReceipt.uuid_record == Matched.uuid_receipt)
    )
    if status_filter == "matched":
        base_stmt = base_stmt.where(Matched.uuid_passport.is_not(None))
    elif status_filter == "unmatched":
        base_stmt = base_stmt.where(Matched.uuid_passport.is_(None))

    total_count = (await db.execute_query(base_stmt.with_only_columns(func.count()).order_by(None), schemas=schemas)).scalar() or 0
    stmt = base_stmt.order_by(models.VerifiedReceipt.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute_query(stmt, schemas=schemas)
    return {
        "items": [dict(row) for row in result.mappings().all()],
        "total_count": int(total_count),
        "page": page,
        "page_size": page_size,
    }


@router.get("/data-mapping/matches/{uuid_receipt}", summary="Get tenant match detail")
@handle_http_error
async def get_match_detail(
    uuid_receipt: str,
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    stmt_base = (
        select(Matched, models.VerifiedReceipt, models.Image.path.label("image_path"))
        .select_from(Matched)
        .join(models.VerifiedReceipt, models.VerifiedReceipt.uuid_record == Matched.uuid_receipt)
        .join(models.Image, models.Image.hash == models.VerifiedReceipt.hash_img, isouter=True)
        .where(Matched.uuid_receipt == uuid_receipt)
    )
    row = (await db.execute_query(stmt_base, schemas=schemas)).first()
    if not row or row[0] is None or row[1] is None:
        raise HTTPException(status_code=404, detail="해당 영수증의 매칭 결과를 찾을 수 없습니다.")

    matched, vr, image_path = row[0], row[1], row[2]
    receipt = {
        "uuid_record": vr.uuid_record,
        "dutyfree_company": vr.dutyfree_company,
        "group_no": vr.group_no,
        "receipt_no": vr.receipt_no,
        "country_code": vr.country_code,
        "passport_no": vr.passport_no,
        "name": vr.name,
        "coordinate_verified": vr.coordinate,
        "hash_img": vr.hash_img,
        "image_path": image_path,
    }
    possible_passports = getattr(matched, "possible_passports", None) or []
    ranks = getattr(matched, "ranks", None) or [float(i) for i in range(len(possible_passports))]
    candidates: list[dict[str, Any]] = []
    if possible_passports:
        result_candidates = await db.execute_query(
            _passport_candidate_select().where(models.VerifiedPassport.uuid_record.in_(possible_passports)),
            schemas=schemas,
        )
        by_uuid = {str(r["uuid_record"]): dict(r) for r in result_candidates.mappings().all()}
        for idx, uuid_p in enumerate(possible_passports):
            candidate = by_uuid.get(str(uuid_p))
            if candidate:
                candidate["rank"] = ranks[idx] if idx < len(ranks) else float(idx)
                candidates.append(candidate)
        candidates = sorted(candidates, key=lambda x: (x.get("rank", 0), x.get("uuid_record", "")))

    current_match = None
    current_uuid_passport = getattr(matched, "uuid_passport", None)
    if current_uuid_passport:
        current_match = next((c for c in candidates if str(c.get("uuid_record")) == str(current_uuid_passport)), None)
        if current_match is None:
            result_current = await db.execute_query(
                _passport_candidate_select().where(models.VerifiedPassport.uuid_record == current_uuid_passport),
                schemas=schemas,
            )
            row_current = result_current.mappings().first()
            if row_current:
                current_match = dict(row_current)
                current_match["rank"] = 0.0
    return {"receipt": receipt, "current_match": current_match, "candidates": candidates}


@router.get("/data-mapping/receipts", summary="List receipt OCR or verification rows")
@handle_http_error
async def list_receipts_for_review(
    is_completed: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    if not is_completed:
        order_column = models.OcrReceipt.id
        stmt = (
            select(
                models.OcrReceipt.id.label("id"),
                models.OcrReceipt.uuid_record.label("uuid_record"),
                models.OcrReceipt.dutyfree_company.label("dutyfree_company"),
                models.OcrReceipt.group_no.label("group_no"),
                models.OcrReceipt.receipt_no.label("receipt_no"),
                models.OcrReceipt.country_code.label("country_code"),
                models.OcrReceipt.passport_no.label("passport_no"),
                models.OcrReceipt.purchaser.label("purchaser"),
                models.OcrReceipt.coordinate.label("coordinate_ocr"),
                models.OcrReceipt.hash_img.label("hash_img"),
                models.Image.path.label("image_path"),
            )
            .join(models.Image, models.Image.hash == models.OcrReceipt.hash_img, isouter=True)
            .where(models.OcrReceipt.is_processed.is_(False))
        )
    else:
        order_column = models.VerifiedReceipt.id
        stmt = (
            select(
                models.VerifiedReceipt.id.label("id"),
                models.VerifiedReceipt.uuid_record.label("uuid_record"),
                models.VerifiedReceipt.dutyfree_company.label("dutyfree_company"),
                models.VerifiedReceipt.group_no.label("group_no"),
                models.VerifiedReceipt.receipt_no.label("receipt_no"),
                models.VerifiedReceipt.passport_no.label("passport_no"),
                models.VerifiedReceipt.name.label("purchaser"),
                models.VerifiedReceipt.hash_img.label("hash_img"),
                models.Image.path.label("image_path"),
                models.VerifiedReceipt.coordinate.label("coordinate_verified"),
                models.OcrReceipt.coordinate.label("coordinate_ocr"),
            )
            .join(models.Image, models.Image.hash == models.VerifiedReceipt.hash_img, isouter=True)
            .join(models.OcrReceipt, models.OcrReceipt.hash_img == models.VerifiedReceipt.hash_img, isouter=True)
            .where(models.VerifiedReceipt.is_verified.is_(True))
        )
    result = await db.execute_query(stmt.order_by(order_column.desc()).offset(skip).limit(limit), schemas=schemas)
    return [
        {
            "id": row.get("id"),
            "uuid_record": row.get("uuid_record"),
            "source": "verified" if is_completed else "ocr",
            "dutyfree_company": row.get("dutyfree_company"),
            "group_no": row.get("group_no"),
            "receipt_no": row.get("receipt_no"),
            "country_code": row.get("country_code"),
            "passport_no": row.get("passport_no"),
            "purchaser": row.get("purchaser"),
            "is_completed": is_completed,
            "image": _image(row),
        }
        for row in result.mappings().all()
    ]


@router.get("/data-mapping/passports", summary="List passport OCR or verification rows")
@handle_http_error
async def list_passports_for_review(
    is_completed: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    if not is_completed:
        order_column = models.OcrPassport.id
        stmt = (
            select(
                models.OcrPassport.id.label("id"),
                models.OcrPassport.uuid_record.label("uuid_record"),
                models.OcrPassport.country_code.label("country_code"),
                models.OcrPassport.passport_no.label("passport_no"),
                models.OcrPassport.name.label("name"),
                models.OcrPassport.coordinate.label("coordinate_ocr"),
                models.OcrPassport.hash_img.label("hash_img"),
                models.Image.path.label("image_path"),
            )
            .join(models.Image, models.Image.hash == models.OcrPassport.hash_img, isouter=True)
            .where(models.OcrPassport.is_processed.is_(False))
        )
    else:
        order_column = models.VerifiedPassport.id
        stmt = (
            select(
                models.VerifiedPassport.id.label("id"),
                models.VerifiedPassport.uuid_record.label("uuid_record"),
                models.VerifiedPassport.country_code.label("country_code"),
                models.VerifiedPassport.passport_no.label("passport_no"),
                models.VerifiedPassport.name.label("name"),
                models.VerifiedPassport.hash_img.label("hash_img"),
                models.Image.path.label("image_path"),
                models.VerifiedPassport.coordinate.label("coordinate_verified"),
                models.OcrPassport.coordinate.label("coordinate_ocr"),
            )
            .join(models.Image, models.Image.hash == models.VerifiedPassport.hash_img, isouter=True)
            .join(models.OcrPassport, models.OcrPassport.hash_img == models.VerifiedPassport.hash_img, isouter=True)
            .where(models.VerifiedPassport.is_verified.is_(True))
        )
    result = await db.execute_query(stmt.order_by(order_column.desc()).offset(skip).limit(limit), schemas=schemas)
    return [
        {
            "id": row.get("id"),
            "uuid_record": row.get("uuid_record"),
            "source": "verified" if is_completed else "ocr",
            "country_code": row.get("country_code"),
            "passport_no": row.get("passport_no"),
            "name": row.get("name"),
            "is_completed": is_completed,
            "image": _image(row),
        }
        for row in result.mappings().all()
    ]
