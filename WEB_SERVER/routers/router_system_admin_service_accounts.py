###########################################
# Module name : router_system_admin_service_accounts.py
# Module functions : 시스템 어드민 서비스 어카운트 API
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.24
# Supported by : Cursor AI
############################################

from datetime import datetime

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, text, update

from CUSTOMIZED.cust_deco_error import handle_http_error
from DATABASE import models
from DATABASE.dbms import DBManager
from DATABASE.models.public_model import ServiceAccount, ServiceAccountRole
from WEB_SERVER.auth.dependencies import get_current_superuser
from WEB_SERVER.routers.settings import get_db_manager

router = APIRouter()


class ServiceAccountCreateRequest(BaseModel):
    alias: str | None = None
    e_mail: EmailStr
    password: str
    role: str
    description: str | None = None
    is_active: bool = True


class ServiceAccountUpdateRequest(BaseModel):
    alias: str | None = None
    e_mail: EmailStr | None = None
    password: str | None = None
    role: str | None = None
    description: str | None = None
    is_active: bool | None = None


def _service_account_response(account: ServiceAccount) -> dict:
    account_dict = account.to_dict()
    account_dict.pop("password", None)
    db_created_at = account_dict.pop("db_created_at", None)
    db_updated_at = account_dict.pop("db_updated_at", None)
    account_dict["created_at"] = db_created_at.isoformat() if db_created_at else None
    account_dict["updated_at"] = db_updated_at.isoformat() if db_updated_at else None
    return account_dict


@router.get("/service-accounts", summary="서비스 어카운트 목록 조회", description="모든 서비스 어카운트 목록을 조회합니다.")
@handle_http_error
async def get_service_accounts(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 레코드 수"),
    role: str | None = Query(None, description="역할 필터"),
    is_active: bool | None = Query(None, description="활성화 여부 필터"),
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]

    stmt = select(ServiceAccount)
    if role:
        stmt = stmt.where(ServiceAccount.role == role)
    if is_active is not None:
        stmt = stmt.where(ServiceAccount.is_active == is_active)
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute_query(stmt, schemas=schemas)
    accounts = result.scalars().all()

    return {
        "service_accounts": [_service_account_response(account) for account in accounts],
        "total": len(accounts),
        "skip": skip,
        "limit": limit,
    }


@router.get("/service-accounts/{account_id}", summary="서비스 어카운트 상세 조회", description="특정 서비스 어카운트의 상세 정보를 조회합니다.")
@handle_http_error
async def get_service_account_detail(
    account_id: int,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]

    stmt = select(ServiceAccount).where(ServiceAccount.id == account_id)
    result = await db.execute_query(stmt, schemas=schemas)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="서비스 어카운트를 찾을 수 없습니다",
        )

    return _service_account_response(account)


@router.post("/service-accounts", summary="서비스 어카운트 생성", description="새로운 서비스 어카운트를 생성합니다.")
@handle_http_error
async def create_service_account(
    account_data: ServiceAccountCreateRequest,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]

    try:
        role_enum = ServiceAccountRole(account_data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"유효하지 않은 역할입니다: {account_data.role}",
        )

    stmt = select(ServiceAccount).where(ServiceAccount.e_mail == account_data.e_mail)
    result = await db.execute_query(stmt, schemas=schemas)
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 이메일입니다",
        )

    account_df = pd.DataFrame([{
        "alias": account_data.alias,
        "e_mail": account_data.e_mail,
        "password": account_data.password,
        "role": str(role_enum.value),
        "description": account_data.description,
        "is_active": account_data.is_active,
    }])

    await db.upsert_batch(table=ServiceAccount, data=account_df, schemas=schemas)

    stmt = select(ServiceAccount).where(ServiceAccount.e_mail == account_data.e_mail)
    result = await db.execute_query(stmt, schemas=schemas)
    created_account = result.scalar_one()

    return {
        "message": "서비스 어카운트가 등록되었습니다",
        "service_account": _service_account_response(created_account),
        "created_at": datetime.now().isoformat(),
        "created_by": current_user.e_mail,
    }


@router.put("/service-accounts/{account_id}", summary="서비스 어카운트 수정", description="서비스 어카운트 정보를 수정합니다.")
@handle_http_error
async def update_service_account(
    account_id: int,
    update_data: ServiceAccountUpdateRequest,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]

    stmt = select(ServiceAccount).where(ServiceAccount.id == account_id)
    result = await db.execute_query(stmt, schemas=schemas)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="서비스 어카운트를 찾을 수 없습니다",
        )

    update_dict = {}
    if update_data.alias is not None:
        update_dict["alias"] = update_data.alias
    if update_data.e_mail is not None:
        stmt = select(ServiceAccount).where(
            ServiceAccount.e_mail == update_data.e_mail,
            ServiceAccount.id != account_id,
        )
        result = await db.execute_query(stmt, schemas=schemas)
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 존재하는 이메일입니다",
            )
        update_dict["e_mail"] = update_data.e_mail
    if update_data.password is not None:
        update_dict["password"] = update_data.password
    if update_data.role is not None:
        try:
            role_enum = ServiceAccountRole(update_data.role)
            update_dict["role"] = str(role_enum.value)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"유효하지 않은 역할입니다: {update_data.role}",
            )
    if update_data.description is not None:
        update_dict["description"] = update_data.description
    if update_data.is_active is not None:
        update_dict["is_active"] = update_data.is_active

    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 데이터가 없습니다",
        )

    stmt = update(ServiceAccount).where(ServiceAccount.id == account_id).values(**update_dict)
    await db.execute_query(stmt, schemas=schemas)

    stmt = select(ServiceAccount).where(ServiceAccount.id == account_id)
    result = await db.execute_query(stmt, schemas=schemas)
    updated_account = result.scalar_one()

    return {
        "message": "서비스 어카운트 정보가 수정되었습니다",
        "service_account": _service_account_response(updated_account),
        "updated_at": datetime.now().isoformat(),
        "updated_by": current_user.e_mail,
    }


@router.delete("/service-accounts/{account_id}", summary="서비스 어카운트 삭제", description="서비스 어카운트를 삭제합니다.")
@handle_http_error
async def delete_service_account(
    account_id: int,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    schemas = ["public"]

    stmt = select(ServiceAccount).where(ServiceAccount.id == account_id)
    result = await db.execute_query(stmt, schemas=schemas)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="서비스 어카운트를 찾을 수 없습니다",
        )

    stmt = text("DELETE FROM public.service_account WHERE id = :account_id")
    await db.execute_query(stmt, {"account_id": account_id}, schemas=schemas)

    return {
        "message": "서비스 어카운트가 삭제되었습니다",
        "account_id": account_id,
        "deleted_at": datetime.now().isoformat(),
        "deleted_by": current_user.e_mail,
    }
