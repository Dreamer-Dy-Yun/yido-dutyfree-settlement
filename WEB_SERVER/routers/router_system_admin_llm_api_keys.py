###########################################
# Module name : router_system_admin_llm_api_keys.py
# Module functions : 시스템 어드민 LLM API Key API
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.24
# Supported by : Cursor AI
############################################

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, select, update

from CUSTOMIZED.cust_deco_error import handle_http_error
from DATABASE import models
from DATABASE.dbms import DBManager
from DATABASE.models.public_model import LLM_API_Key
from WEB_SERVER.auth.dependencies import get_current_superuser
from WEB_SERVER.routers.settings import get_db_manager

router = APIRouter()


class LLMApiKeyCreateRequest(BaseModel):
    """public.llm_api_key requires purpose."""

    purpose: str = Field(..., min_length=1, description="LLM 용도 (예: OCR)")
    llm_provider: str
    llm_model: str
    api_key: str
    is_active: bool = False

    @field_validator("purpose", mode="before")
    @classmethod
    def strip_purpose(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v


class LLMApiKeyUpdateRequest(BaseModel):
    purpose: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    api_key: str | None = None
    is_active: bool | None = None


def _llm_api_key_response(row: LLM_API_Key) -> dict:
    row_dict = row.to_dict()
    row_dict["api_key"] = LLM_API_Key.mask_api_key(row.api_key)
    return row_dict


@router.get("/llm-api-keys", summary="LLM API Key 목록 조회", description="LLM API Key 목록을 조회합니다.")
@handle_http_error
async def get_llm_api_keys(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 레코드 수"),
    llm_provider: str | None = Query(None, description="LLM 제공사 필터"),
    is_active: bool | None = Query(None, description="활성화 여부 필터"),
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]
    stmt = select(LLM_API_Key)
    if llm_provider:
        stmt = stmt.where(LLM_API_Key.llm_provider == llm_provider)
    if is_active is not None:
        stmt = stmt.where(LLM_API_Key.is_active == is_active)
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute_query(stmt, schemas=schemas)
    rows = result.scalars().all()
    return {
        "llm_api_keys": [_llm_api_key_response(row) for row in rows],
        "total": len(rows),
        "skip": skip,
        "limit": limit,
    }


@router.get("/llm-api-keys/{api_key_id}", summary="LLM API Key 상세 조회", description="특정 LLM API Key를 조회합니다.")
@handle_http_error
async def get_llm_api_key_detail(
    api_key_id: int,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]
    stmt = select(LLM_API_Key).where(LLM_API_Key.id == api_key_id)
    result = await db.execute_query(stmt, schemas=schemas)
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LLM API Key를 찾을 수 없습니다")
    return _llm_api_key_response(row)


@router.post("/llm-api-keys", summary="LLM API Key 생성", description="새 LLM API Key를 등록합니다.")
@handle_http_error
async def create_llm_api_key(
    body: LLMApiKeyCreateRequest,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]
    stmt_dup = select(LLM_API_Key).where(LLM_API_Key.api_key == body.api_key)
    result_dup = await db.execute_query(stmt_dup, schemas=schemas)
    if result_dup.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 등록된 API Key입니다")

    df = pd.DataFrame([body.model_dump()])
    await db.upsert_batch(table=LLM_API_Key, data=df, schemas=schemas)

    stmt = select(LLM_API_Key).where(LLM_API_Key.api_key == body.api_key)
    result = await db.execute_query(stmt, schemas=schemas)
    created = result.scalar_one()
    return {"message": "LLM API Key가 등록되었습니다", "llm_api_key": _llm_api_key_response(created)}


@router.put("/llm-api-keys/{api_key_id}", summary="LLM API Key 수정", description="LLM API Key 정보를 수정합니다.")
@handle_http_error
async def update_llm_api_key(
    api_key_id: int,
    body: LLMApiKeyUpdateRequest,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]
    stmt = select(LLM_API_Key).where(LLM_API_Key.id == api_key_id)
    result = await db.execute_query(stmt, schemas=schemas)
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LLM API Key를 찾을 수 없습니다")

    update_dict = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="수정할 데이터가 없습니다")

    if "api_key" in update_dict:
        stmt_dup = select(LLM_API_Key).where(
            LLM_API_Key.api_key == update_dict["api_key"],
            LLM_API_Key.id != api_key_id,
        )
        result_dup = await db.execute_query(stmt_dup, schemas=schemas)
        if result_dup.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 등록된 API Key입니다")

    stmt_update = update(LLM_API_Key).where(LLM_API_Key.id == api_key_id).values(**update_dict)
    await db.execute_query(stmt_update, schemas=schemas)

    stmt_after = select(LLM_API_Key).where(LLM_API_Key.id == api_key_id)
    result_after = await db.execute_query(stmt_after, schemas=schemas)
    updated_row = result_after.scalar_one()
    return {"message": "LLM API Key가 수정되었습니다", "llm_api_key": _llm_api_key_response(updated_row)}


@router.delete("/llm-api-keys/{api_key_id}", summary="LLM API Key 삭제", description="LLM API Key를 삭제합니다.")
@handle_http_error
async def delete_llm_api_key(
    api_key_id: int,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]
    stmt = select(LLM_API_Key).where(LLM_API_Key.id == api_key_id)
    result = await db.execute_query(stmt, schemas=schemas)
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LLM API Key를 찾을 수 없습니다")

    stmt_del = delete(LLM_API_Key).where(LLM_API_Key.id == api_key_id)
    await db.execute_query(stmt_del, schemas=schemas)
    return {"message": "LLM API Key가 삭제되었습니다", "api_key_id": api_key_id}
