###########################################
# Module name : router_system_admin_prompts.py
# Module functions : 시스템 어드민 Prompt API
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.24
# Supported by : Cursor AI
############################################

import hashlib
from typing import Literal

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import delete, select, update

from CUSTOMIZED.cust_deco_error import handle_http_error
from DATABASE import models
from DATABASE.dbms import DBManager
from DATABASE.models.public_model import Prompt
from WEB_SERVER.auth.dependencies import get_current_superuser
from WEB_SERVER.routers.settings import get_db_manager

router = APIRouter()


class PromptCreateRequest(BaseModel):
    purpose: str
    type: Literal["SYSTEM", "USER"]
    prompt: str
    note: str | None = None
    is_active: bool = False


class PromptUpdateRequest(BaseModel):
    purpose: str | None = None
    type: Literal["SYSTEM", "USER"] | None = None
    prompt: str | None = None
    note: str | None = None
    is_active: bool | None = None


@router.get("/prompts", summary="Prompt 목록 조회", description="Prompt 목록을 조회합니다.")
@handle_http_error
async def get_prompts(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 레코드 수"),
    purpose: str | None = Query(None, description="프롬프트 목적 필터"),
    type: str | None = Query(None, description="프롬프트 타입 필터"),
    is_active: bool | None = Query(None, description="활성화 여부 필터"),
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]
    stmt = select(Prompt)
    if purpose:
        stmt = stmt.where(Prompt.purpose == purpose)
    if type:
        stmt = stmt.where(Prompt.type == type)
    if is_active is not None:
        stmt = stmt.where(Prompt.is_active == is_active)
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute_query(stmt, schemas=schemas)
    rows = result.scalars().all()
    return {
        "prompts": [row.to_dict() for row in rows],
        "total": len(rows),
        "skip": skip,
        "limit": limit,
    }


@router.get("/prompts/{prompt_id}", summary="Prompt 상세 조회", description="특정 Prompt를 조회합니다.")
@handle_http_error
async def get_prompt_detail(
    prompt_id: int,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]
    stmt = select(Prompt).where(Prompt.id == prompt_id)
    result = await db.execute_query(stmt, schemas=schemas)
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt를 찾을 수 없습니다")
    return row.to_dict()


@router.post("/prompts", summary="Prompt 생성", description="새 Prompt를 등록합니다.")
@handle_http_error
async def create_prompt(
    body: PromptCreateRequest,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]
    hash_prompt = hashlib.sha256(body.prompt.encode("utf-8")).hexdigest()
    stmt_dup = select(Prompt).where(Prompt.hash == hash_prompt)
    result_dup = await db.execute_query(stmt_dup, schemas=schemas)
    if result_dup.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 등록된 Prompt입니다")

    df = pd.DataFrame([{
        "hash": hash_prompt,
        "purpose": body.purpose,
        "type": body.type,
        "prompt": body.prompt,
        "note": body.note,
        "is_active": body.is_active,
    }])
    await db.upsert_batch(table=Prompt, data=df, schemas=schemas)

    stmt = select(Prompt).where(Prompt.hash == hash_prompt)
    result = await db.execute_query(stmt, schemas=schemas)
    created = result.scalar_one()
    return {"message": "Prompt가 등록되었습니다", "prompt": created.to_dict()}


@router.put("/prompts/{prompt_id}", summary="Prompt 수정", description="Prompt 정보를 수정합니다.")
@handle_http_error
async def update_prompt(
    prompt_id: int,
    body: PromptUpdateRequest,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]
    stmt = select(Prompt).where(Prompt.id == prompt_id)
    result = await db.execute_query(stmt, schemas=schemas)
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt를 찾을 수 없습니다")

    update_dict = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="수정할 데이터가 없습니다")

    if "prompt" in update_dict:
        new_hash = hashlib.sha256(update_dict["prompt"].encode("utf-8")).hexdigest()
        stmt_dup = select(Prompt).where(
            Prompt.hash == new_hash,
            Prompt.id != prompt_id,
        )
        result_dup = await db.execute_query(stmt_dup, schemas=schemas)
        if result_dup.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 등록된 Prompt입니다")
        update_dict["hash"] = new_hash

    stmt_update = update(Prompt).where(Prompt.id == prompt_id).values(**update_dict)
    await db.execute_query(stmt_update, schemas=schemas)

    stmt_after = select(Prompt).where(Prompt.id == prompt_id)
    result_after = await db.execute_query(stmt_after, schemas=schemas)
    updated_row = result_after.scalar_one()
    return {"message": "Prompt가 수정되었습니다", "prompt": updated_row.to_dict()}


@router.delete("/prompts/{prompt_id}", summary="Prompt 삭제", description="Prompt를 삭제합니다.")
@handle_http_error
async def delete_prompt(
    prompt_id: int,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]
    stmt = select(Prompt).where(Prompt.id == prompt_id)
    result = await db.execute_query(stmt, schemas=schemas)
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt를 찾을 수 없습니다")

    stmt_del = delete(Prompt).where(Prompt.id == prompt_id)
    await db.execute_query(stmt_del, schemas=schemas)
    return {"message": "Prompt가 삭제되었습니다", "prompt_id": prompt_id}
