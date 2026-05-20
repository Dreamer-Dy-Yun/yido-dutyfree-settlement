from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete as sql_delete, select, tuple_, update as sql_update

from CUSTOMIZED.cust_deco_error import handle_http_error
from DATABASE import models
from DATABASE.dbms import DBManager
from WEB_SERVER.auth.dependencies import get_current_user
from WEB_SERVER.routers.settings import get_db_manager
from WEB_SERVER.routers.tenant_helpers import _fetch_verify_source, _get_current_tenant_schemas, _mark_ocr_processed_if_needed, _merge_passport_fk_and_replace, _merge_receipt_fk_and_replace, _normalize_receipt_no, _verified_row_common
from WEB_SERVER.routers.tenant_schemas import BulkVerifyPassportsRequest, BulkVerifyReceiptsRequest, PassportVerifyRequest, ReceiptVerifyRequest, VerifyDeleteRequest
from WEB_SERVER.services.service_verified_archive import archive_verified_row_by_uuid

router = APIRouter()


def _source(value: str | None) -> str:
    source = (value or "").lower()
    if source not in ("ocr", "verified"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="source must be 'ocr' or 'verified'.")
    return source


def _common(current_user: models.User, source_row: Any, coordinate: Any, rotation: Any, corrected: bool, mode: str) -> dict:
    return _verified_row_common(
        current_user,
        getattr(source_row, "hash_img", None),
        coordinate,
        rotation,
        corrected,
        getattr(source_row, "uuid_batch", None) or "",
        getattr(source_row, "uuid_record", None) or "",
        verification_mode=mode,
    )


async def _delete_verified_or_mark_ocr(
    db: DBManager,
    schemas: dict,
    current_user: models.User,
    payload: VerifyDeleteRequest,
    ocr_model: Any,
    verified_model: Any,
    archive_model: Any,
    not_found_ocr: str,
    not_found_verified: str,
    deleted_message: str,
    skipped_message: str,
):
    ocr_row, verified_row = await _fetch_verify_source(
        db, schemas, _source(payload.source), payload.id, ocr_model, verified_model, not_found_ocr, not_found_verified
    )
    if verified_row is not None:
        target_uuid = str(getattr(verified_row, "uuid_record", "") or "").strip()
        if not target_uuid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verified uuid_record not found.")
        await archive_verified_row_by_uuid(db, schemas, verified_model, archive_model, target_uuid, current_user)
        await db.execute_query(sql_delete(verified_model).where(verified_model.uuid_record == target_uuid), schemas=schemas)
        return {"message": deleted_message, "uuid_record": target_uuid}
    if ocr_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_ocr)
    await db.execute_query(
        sql_update(ocr_model)
        .where(ocr_model.id == ocr_row.id)
        .values(is_processed=True, db_updated_by=str(getattr(current_user, "id", ""))),
        schemas=schemas,
    )
    return {"message": skipped_message, "uuid_record": str(getattr(ocr_row, "uuid_record", "") or "").strip()}


@router.post("/data-mapping/receipts/verify", summary="Verify or correct receipt row")
@handle_http_error
async def verify_receipt(
    payload: ReceiptVerifyRequest,
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    ocr_row, verified_row = await _fetch_verify_source(
        db, schemas, _source(payload.source), payload.id, models.OcrReceipt, models.VerifiedReceipt,
        "OCR receipt not found.", "Verified receipt not found.",
    )
    source_row = ocr_row or verified_row
    dutyfree_company = (payload.dutyfree_company or "").strip()
    receipt_no = (payload.receipt_no or "").strip()
    purchaser = (payload.purchaser or "").strip()
    corrected = any([
        dutyfree_company != (getattr(source_row, "dutyfree_company", None) or ""),
        receipt_no != (getattr(source_row, "receipt_no", None) or ""),
        (payload.country_code or "").strip() != (getattr(source_row, "country_code", None) or ""),
        (payload.passport_no or "").strip() != (getattr(source_row, "passport_no", None) or ""),
        purchaser != ((getattr(source_row, "purchaser", None) or getattr(source_row, "name", None)) or ""),
    ])
    row = {
        "dutyfree_company": dutyfree_company,
        "group_no": (payload.group_no or "").strip(),
        "receipt_no": receipt_no,
        "normalized_receipt_no": _normalize_receipt_no(receipt_no),
        "country_code": (payload.country_code or "").strip(),
        "passport_no": (payload.passport_no or "").strip(),
        "name": purchaser,
        **_common(current_user, source_row, payload.coordinate, payload.rotation, corrected, "single"),
    }
    try:
        await db.upsert_batch(table=models.VerifiedReceipt, data=pd.DataFrame([row]), schemas=schemas, conflict_cols=["uuid_record"])
    except Exception as exc:
        existing_uuid = (
            await db.execute_query(
                select(models.VerifiedReceipt.uuid_record)
                .where(models.VerifiedReceipt.dutyfree_company == dutyfree_company)
                .where(models.VerifiedReceipt.receipt_no == receipt_no),
                schemas=schemas,
            )
        ).scalar_one_or_none()
        if existing_uuid and row.get("uuid_record") and str(existing_uuid) != str(row["uuid_record"]):
            if payload.force_merge:
                await _merge_receipt_fk_and_replace(db=db, schemas=schemas, old_uuid=str(existing_uuid), row_new=row)
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "VERIFIED_RECEIPT_DUPLICATE", "existing_uuid": str(existing_uuid), "current_uuid": str(row["uuid_record"]), "force_merge_required": True},
                )
        else:
            raise exc
    await _mark_ocr_processed_if_needed(db, schemas, ocr_row, models.OcrReceipt, current_user)
    return {"message": "영수증 정보가 검증 저장되었습니다.", "dutyfree_company": payload.dutyfree_company, "receipt_no": payload.receipt_no, "is_corrected": corrected}


@router.delete("/data-mapping/receipts/verify", summary="Delete or skip receipt verification row")
@handle_http_error
async def delete_receipt(
    payload: VerifyDeleteRequest,
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    return await _delete_verified_or_mark_ocr(
        db, schemas, current_user, payload, models.OcrReceipt, models.VerifiedReceipt, models.ArchiveReceipt,
        "OCR receipt not found.", "Verified receipt not found.", "검증 영수증이 삭제되었습니다.", "OCR 영수증이 미완료 목록에서 제외되었습니다.",
    )


@router.post("/data-mapping/receipts/bulk-verify", summary="Bulk verify receipt rows")
@handle_http_error
async def bulk_verify_receipts(
    payload: BulkVerifyReceiptsRequest,
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    if not payload.ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receipt id list is empty.")
    result = await db.execute_query(
        select(models.OcrReceipt).where(models.OcrReceipt.uuid_record.in_(payload.ids)).where(models.OcrReceipt.is_processed.is_(False)),
        schemas=schemas,
    )
    rows_src = result.scalars().all()
    if not rows_src:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipts not found.")
    rows = [{
        "dutyfree_company": (orc.dutyfree_company or "").strip(),
        "group_no": (orc.group_no or "").strip(),
        "receipt_no": (orc.receipt_no or "").strip(),
        "normalized_receipt_no": _normalize_receipt_no((orc.receipt_no or "").strip()),
        "country_code": (orc.country_code or "").strip(),
        "passport_no": (orc.passport_no or "").strip(),
        "name": (orc.purchaser or "").strip(),
        **_common(current_user, orc, orc.coordinate, None, False, "bulk"),
    } for orc in rows_src]
    df_rows = pd.DataFrame(rows).drop_duplicates(subset=["uuid_record"], keep="last").drop_duplicates(subset=["dutyfree_company", "receipt_no"], keep="last")
    await db.upsert_batch(table=models.VerifiedReceipt, data=df_rows, schemas=schemas, conflict_cols=["uuid_record"])
    await db.execute_query(sql_update(models.OcrReceipt).where(models.OcrReceipt.uuid_record.in_(payload.ids)).values(is_processed=True), schemas=schemas)
    return {"message": f"{len(rows)}건의 영수증이 일괄 확인 처리되었습니다.", "count": len(rows)}


@router.post("/data-mapping/passports/verify", summary="Verify or correct passport row")
@handle_http_error
async def verify_passport(
    payload: PassportVerifyRequest,
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    if payload.passport_no and len(payload.passport_no) > 9:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passport number must be 9 characters or fewer.")
    ocr_row, verified_row = await _fetch_verify_source(
        db, schemas, _source(payload.source), payload.id, models.OcrPassport, models.VerifiedPassport,
        "OCR passport not found.", "Verified passport not found.",
    )
    source_row = ocr_row or verified_row
    country_code = (payload.country_code or "").strip()
    passport_no = (payload.passport_no or "").strip()
    name = (payload.name or "").strip()
    corrected = any([
        country_code != (getattr(source_row, "country_code", None) or ""),
        passport_no != (getattr(source_row, "passport_no", None) or ""),
        name != (getattr(source_row, "name", None) or ""),
    ])
    row = {"country_code": country_code, "passport_no": passport_no, "name": name, **_common(current_user, source_row, payload.coordinate, payload.rotation, corrected, "single")}
    try:
        await db.upsert_batch(table=models.VerifiedPassport, data=pd.DataFrame([row]), schemas=schemas, conflict_cols=["uuid_record"])
    except Exception as exc:
        existing_uuid = (
            await db.execute_query(
                select(models.VerifiedPassport.uuid_record)
                .where(models.VerifiedPassport.country_code == country_code)
                .where(models.VerifiedPassport.passport_no == passport_no)
                .where(models.VerifiedPassport.uuid_batch == row.get("uuid_batch")),
                schemas=schemas,
            )
        ).scalar_one_or_none()
        if existing_uuid and row.get("uuid_record") and str(existing_uuid) != str(row["uuid_record"]):
            if payload.force_merge:
                await _merge_passport_fk_and_replace(db=db, schemas=schemas, old_uuid=str(existing_uuid), row_new=row)
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "VERIFIED_PASSPORT_DUPLICATE", "existing_uuid": str(existing_uuid), "current_uuid": str(row["uuid_record"]), "force_merge_required": True},
                )
        else:
            raise exc
    await _mark_ocr_processed_if_needed(db, schemas, ocr_row, models.OcrPassport, current_user)
    return {"message": "여권 정보가 검증 저장되었습니다.", "country_code": payload.country_code, "passport_no": payload.passport_no, "is_corrected": corrected}


@router.delete("/data-mapping/passports/verify", summary="Delete or skip passport verification row")
@handle_http_error
async def delete_passport(
    payload: VerifyDeleteRequest,
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    return await _delete_verified_or_mark_ocr(
        db, schemas, current_user, payload, models.OcrPassport, models.VerifiedPassport, models.ArchivePassport,
        "OCR passport not found.", "Verified passport not found.", "검증 여권이 삭제되었습니다.", "OCR 여권이 미완료 목록에서 제외되었습니다.",
    )


@router.post("/data-mapping/passports/bulk-verify", summary="Bulk verify passport rows")
@handle_http_error
async def bulk_verify_passports(
    payload: BulkVerifyPassportsRequest,
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    if not payload.ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passport id list is empty.")
    result = await db.execute_query(
        select(models.OcrPassport).where(models.OcrPassport.uuid_record.in_(payload.ids)).where(models.OcrPassport.is_processed.is_(False)),
        schemas=schemas,
    )
    rows_src = result.scalars().all()
    if not rows_src:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passports not found.")
    rows = [{
        "country_code": (opc.country_code or "").strip(),
        "passport_no": (opc.passport_no or "").strip(),
        "name": (opc.name or "").strip(),
        **_common(current_user, opc, opc.coordinate, None, False, "bulk"),
    } for opc in rows_src]
    df_rows = pd.DataFrame(rows).drop_duplicates(subset=["uuid_record"], keep="last").drop_duplicates(subset=["country_code", "passport_no", "uuid_batch"], keep="last")
    triples = list(zip(df_rows["country_code"].astype(str), df_rows["passport_no"].astype(str), df_rows["uuid_batch"].astype(str)))
    existing_by_triple: dict[tuple[str, str, str], str] = {}
    if triples:
        res_vp = await db.execute_query(
            select(models.VerifiedPassport.country_code, models.VerifiedPassport.passport_no, models.VerifiedPassport.uuid_batch, models.VerifiedPassport.uuid_record)
            .where(tuple_(models.VerifiedPassport.country_code, models.VerifiedPassport.passport_no, models.VerifiedPassport.uuid_batch).in_(triples)),
            schemas=schemas,
        )
        existing_by_triple = {(str(cc), str(pn), str(ub)): str(ur) if ur is not None else "" for cc, pn, ub, ur in res_vp.all()}
    rows_upsert, skipped = [], []
    for rec in df_rows.to_dict("records"):
        key = (str(rec.get("country_code") or ""), str(rec.get("passport_no") or ""), str(rec.get("uuid_batch") or ""))
        existing_uuid = existing_by_triple.get(key)
        cand_uuid = str(rec.get("uuid_record") or "")
        if existing_uuid and existing_uuid != cand_uuid:
            skipped.append({"uuid_record": cand_uuid, "country_code": key[0], "passport_no": key[1], "uuid_batch": key[2], "existing_uuid_record": existing_uuid, "reason": "VERIFIED_PASSPORT_TRIPLE_CONFLICT"})
        else:
            rows_upsert.append(rec)
    upsert_count = 0
    if rows_upsert:
        df_upsert = pd.DataFrame(rows_upsert)
        await db.upsert_batch(table=models.VerifiedPassport, data=df_upsert, schemas=schemas, conflict_cols=["uuid_record"])
        upsert_count = len(df_upsert)
        processed_uuids = [str(u) for u in df_upsert["uuid_record"].dropna().unique().tolist()]
        if processed_uuids:
            await db.execute_query(sql_update(models.OcrPassport).where(models.OcrPassport.uuid_record.in_(processed_uuids)).values(is_processed=True), schemas=schemas)
    return {"message": f"{upsert_count}건의 여권이 일괄 확인 처리되었습니다.", "count": upsert_count, "skipped_count": len(skipped), "skipped": skipped}
