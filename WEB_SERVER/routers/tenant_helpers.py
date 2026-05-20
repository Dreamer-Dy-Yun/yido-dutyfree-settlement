###########################################
# Module name : tenant_helpers.py
# Module functions : Shared helpers for tenant router APIs
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.05.20
# Note : Keep reusable tenant route helpers separate from route handlers.
############################################

from datetime import datetime
from typing import Any, TypeVar
import re

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select, delete as sql_delete, update as sql_update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from DATABASE import models
from DATABASE.dbms import DBManager
from DATABASE.models.base_model import BaseModel as SaBaseModel
from DATABASE.models.public_model import Tenant as PublicTenant

T = TypeVar("T", bound=SaBaseModel)


def _get_current_tenant_schema_from_user(current_user: models.User) -> str:
    """Return tenant schema from the authenticated current_user object."""
    tenant_schema = getattr(current_user, "tenant_schema", None)
    if not tenant_schema:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="유효한 테넌트 스키마를 확인할 수 없습니다.",
        )
    return tenant_schema


def _get_current_tenant_schemas(current_user: models.User) -> list[str]:
    tenant_schema = _get_current_tenant_schema_from_user(current_user)
    return [tenant_schema, "public"]


async def _fetch_verify_source(
    db: "DBManager",
    schemas: list[str],
    source: str,
    payload_id: int,
    ocr_model: type,
    verified_model: type,
    ocr_404_msg: str,
    verified_404_msg: str,
) -> tuple[Any, Any]:
    """Return verification source row as (ocr_row, verified_row)."""
    if source == "ocr":
        stmt = select(ocr_model).where(ocr_model.id == payload_id)
        result = await db.execute_query(stmt, schemas=schemas)
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ocr_404_msg)
        return (row, None)
    stmt = select(verified_model).where(verified_model.id == payload_id)
    result = await db.execute_query(stmt, schemas=schemas)
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=verified_404_msg)
    return (None, row)


async def _fetch_with_id(
    db: DBManager,
    schemas: list[str],
    model: type[T],
    record_id: int,
) -> T | None:
    stmt = select(model).where(model.id == record_id)
    result = await db.execute_query(stmt, schemas=schemas)
    return result.scalar_one_or_none()


def _verified_row_common(
    current_user: models.User,
    hash_img: Any,
    coordinate: Any,
    rotation: Any,
    is_corrected: bool,
    uuid_batch: str,
    uuid_record: str,
    verification_mode: str | None = None,
) -> dict[str, Any]:
    """Common fields for Verified* upsert rows."""
    return {
        "hash_img": hash_img,
        "coordinate": coordinate,
        "rotation": rotation,
        "is_verified": True,
        "is_corrected": is_corrected,
        "verifier_id": getattr(current_user, "id", None),
        "verifier_name": getattr(current_user, "name", None),
        "db_updated_by": str(getattr(current_user, "id", "")),
        "uuid_batch": uuid_batch or "",
        "uuid_record": uuid_record or "",
        "verification_mode": verification_mode,
    }


async def _upsert_verified_row_by_uuid(
    session,
    table_model: type,
    row: dict[str, Any],
) -> None:
    """Upsert one Verified* row by uuid_record."""
    tbl = table_model.__table__
    stmt = pg_insert(tbl).values(**row)
    update_cols = {k: v for k, v in row.items() if k != "uuid_record"}
    stmt = stmt.on_conflict_do_update(
        index_elements=[tbl.c.uuid_record],
        set_=update_cols,
    )
    await session.execute(stmt)


async def _merge_receipt_fk_and_replace(
    db: DBManager,
    schemas: list[str],
    old_uuid: str,
    row_new: dict[str, Any],
) -> None:
    """Replace receipt UUID references, delete old row, then upsert the new row."""
    new_uuid = str(row_new.get("uuid_record") or "").strip()
    if not old_uuid or not new_uuid:
        raise HTTPException(status_code=400, detail="old_uuid/new_uuid가 비어 있습니다.")

    async with db.open_session(schemas=schemas) as session:
        if old_uuid != new_uuid:
            stmt_cnt_new = (
                select(func.count(models.Matched.id))
                .where(models.Matched.uuid_receipt == new_uuid)
            )
            res_cnt_new = await session.execute(stmt_cnt_new)
            has_new_matched = (res_cnt_new.scalar() or 0) > 0

            if has_new_matched:
                await session.execute(
                    sql_delete(models.Matched)
                    .where(models.Matched.uuid_receipt == old_uuid)
                )
            else:
                await session.execute(
                    sql_update(models.Matched)
                    .where(models.Matched.uuid_receipt == old_uuid)
                    .values(uuid_receipt=new_uuid)
                )

        await session.execute(
            sql_update(models.EDI_Unified)
            .where(models.EDI_Unified.uuid_receipt == old_uuid)
            .values(uuid_receipt=new_uuid)
        )
        await session.execute(
            sql_delete(models.VerifiedReceipt)
            .where(models.VerifiedReceipt.uuid_record == old_uuid)
        )
        await _upsert_verified_row_by_uuid(session, models.VerifiedReceipt, row_new)


async def _merge_passport_fk_and_replace(
    db: DBManager,
    schemas: list[str],
    old_uuid: str,
    row_new: dict[str, Any],
) -> None:
    """Replace passport UUID references, delete old row, then upsert the new row."""
    new_uuid = str(row_new.get("uuid_record") or "").strip()
    if not old_uuid or not new_uuid:
        raise HTTPException(status_code=400, detail="old_uuid/new_uuid가 비어 있습니다.")

    async with db.open_session(schemas=schemas) as session:
        await session.execute(
            sql_update(models.Matched)
            .where(models.Matched.uuid_passport == old_uuid)
            .values(uuid_passport=new_uuid)
        )
        await session.execute(
            sql_update(models.EDI_Unified)
            .where(models.EDI_Unified.uuid_passport == old_uuid)
            .values(uuid_passport=new_uuid)
        )
        await session.execute(
            sql_delete(models.VerifiedPassport)
            .where(models.VerifiedPassport.uuid_record == old_uuid)
        )
        await _upsert_verified_row_by_uuid(session, models.VerifiedPassport, row_new)


async def _mark_ocr_processed_if_needed(
    db: "DBManager",
    schemas: list[str],
    ocr_row: Any,
    ocr_model: type,
    current_user: models.User,
) -> None:
    """Mark OCR source row as processed when it exists and is still pending."""
    if ocr_row is None or getattr(ocr_row, "is_processed", False):
        return
    stmt = (
        sql_update(ocr_model)
        .where(ocr_model.id == ocr_row.id)
        .values(is_processed=True, db_updated_by=str(getattr(current_user, "id", "")))
    )
    await db.execute_query(stmt, schemas=schemas)


def _is_valid_email(email: str | None) -> bool:
    if not email:
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()))


def _normalize_receipt_no(receipt_no: str | None) -> str:
    if not receipt_no:
        return ""
    return receipt_no.replace("-", "").replace(" ", "")


def _created_at_range_conditions(model: type[Any], start_date: datetime | None, end_date: datetime | None) -> list[Any]:
    conditions: list[Any] = []
    if start_date:
        conditions.append(model.db_created_at >= start_date)
    if end_date:
        conditions.append(model.db_created_at <= end_date)
    return conditions


async def _count_created_rows(
    db: DBManager,
    schemas: list[str],
    model: type[Any],
    start_date: datetime | None,
    end_date: datetime | None,
) -> int:
    stmt = select(func.count(model.id))
    conditions = _created_at_range_conditions(model, start_date, end_date)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    result = await db.execute_query(stmt, schemas=schemas)
    return int(result.scalar() or 0)


def _tenant_info_response(tenant: PublicTenant) -> dict[str, Any]:
    return {
        "id": tenant.id,
        "name": tenant.name,
        "alias": tenant.alias,
        "country_code": tenant.country_code,
        "business_no": tenant.business_no,
        "contact": tenant.contact,
        "email": tenant.email,
        "address": tenant.address,
        "schema_name": tenant.schema_name,
        "is_active": tenant.is_active,
        "db_created_at": tenant.db_created_at,
        "db_updated_at": tenant.db_updated_at,
    }


async def _get_current_public_tenant(
    current_user: models.User,
    db: DBManager,
) -> PublicTenant:
    tenant_schema = _get_current_tenant_schema_from_user(current_user)
    stmt = select(PublicTenant).where(PublicTenant.schema_name == tenant_schema)
    result = await db.execute_query(stmt, schemas=["public"])
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="현재 테넌트 정보를 찾을 수 없습니다.",
        )
    return tenant
