###########################################
# Module name : router_admin.py
# Module functions : 서비스 제공사 관리자용 API
# Written by : Cursor AI 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.20
# Supported by : Cursor AI
# Note : 서비스 제공사 관리자가 테넌트 승인/거부
############################################

from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import text, select
import secrets
import string

from WEB_SERVER.auth.dependencies import get_current_superuser
from WEB_SERVER.routers.settings import get_tenant_repository, get_db_manager
from WEB_SERVER.auth import get_password_hash
from WEB_SERVER.services.service_email import email_service
from CUSTOMIZED.cust_deco_error import handle_http_error

from DATABASE import models
from DATABASE.models.tenant_model import UserRole, User, OcrPassport, VerifiedPassport, OcrReceipt, VerifiedReceipt, Matched, Image, Prompt, LlmUsage, EdiSilla, EdiLotte
from DATABASE.repositories.authorities import TenantRepository
from DATABASE.dbms import DBManager
import pandas as pd
import os

router = APIRouter(prefix="/api/admin", tags=["서비스 제공사 관리"])


# 요청/응답 스키마
class TenantApprovalRequest(BaseModel):
    reason: str | None = None


class TenantRejectionRequest(BaseModel):
    reason: str


# 테넌트 관리 API
@router.get("/tenants", summary="테넌트 목록 조회", description="모든 테넌트 목록을 조회합니다.")
@handle_http_error
async def get_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: bool | None = Query(None),
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """테넌트 목록 조회"""
    tenants = await tenant_repo.get_all(skip=skip, limit=limit, is_active=is_active)
    return {
        "tenants": tenants,
        "total": len(tenants)
    }


@router.get("/tenants/pending", summary="승인 대기 테넌트 목록", description="승인 대기 중인 테넌트 목록을 조회합니다.")
@handle_http_error
async def get_pending_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """승인 대기 테넌트 목록 조회"""
    tenants = await tenant_repo.get_all(skip=skip, limit=limit, is_active=False)
    return {
        "pending_tenants": tenants,
        "total": len(tenants)
    }


@router.post("/tenants/{tenant_id}/approve", summary="테넌트 승인", description="테넌트를 승인하고 스키마를 생성합니다.")
@handle_http_error
async def approve_tenant(
    tenant_id: int,
    approval_data: TenantApprovalRequest | None = None,
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: DBManager = Depends(get_db_manager),
):
    """테넌트 승인 및 스키마 생성"""
    # 테넌트 조회
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="테넌트를 찾을 수 없습니다"
        )
    
    if tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 승인된 테넌트입니다"
        )
    
    # 1. 스키마 생성
    schema_name = tenant.schema_name
    await db.execute_query(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
    
    # 2. 테넌트 스키마로 전환하여 테이블 생성
    await db.set_schemas([schema_name, "public"])
    
    # BaseModel의 metadata에 모든 테이블이 등록되어 있으므로 create_all 사용
    async with db.async_engine.begin() as conn:
        await conn.execute(text(f'SET search_path TO "{schema_name}", "public"'))
        await conn.run_sync(models.BaseModel.metadata.create_all)
    
    # 3. 테넌트 관리자 계정 생성 (임시 패스워드)
    # 회사 등록 시 입력한 관리자 이메일 사용 (tenant.email 또는 별도 필드 필요)
    # 여기서는 tenant.email을 사용하지만, 실제로는 회사 등록 시 admin_email을 별도로 저장해야 함
    admin_email = tenant.email
    if not admin_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="관리자 이메일이 등록되지 않았습니다"
        )
    
    # 임시 패스워드 생성 (12자리, 영문+숫자+특수문자)
    temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(12))
    hashed_password = get_password_hash(temp_password)
    
    # 관리자 계정 생성
    admin_user_df = pd.DataFrame([{
        "name": tenant.name,  # 임시로 회사명 사용
        "e_mail": admin_email,
        "password": hashed_password,
        "role": UserRole.ADMIN.value,
        "is_active": True,
    }])
    
    await db.upsert_dataframe(User, admin_user_df)
    
    # 4. 승인 메일 발송 (임시 패스워드 포함)
    app_url = os.getenv("APP_URL", "http://localhost:3001")
    password_change_url = f"{app_url}/change-password?token=temp&email={admin_email}"
    
    # TODO: 승인 메일 템플릿 생성 및 발송
    # email_service.set_approval_email(...).send()
    
    # 테넌트 활성화
    await tenant_repo.update(tenant_id, {"is_active": True})
    
    return {
        "message": "테넌트가 승인되었습니다",
        "tenant_id": tenant_id,
        "schema_name": tenant.schema_name,
        "admin_email": admin_email,
        "temp_password": temp_password,  # 실제로는 메일로만 전송해야 함
        "password_change_url": password_change_url,
        "approved_at": datetime.now()
    }


@router.post("/tenants/{tenant_id}/reject", summary="테넌트 거부", description="테넌트 등록을 거부합니다.")
@handle_http_error
async def reject_tenant(
    tenant_id: int,
    rejection_data: TenantRejectionRequest,
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """테넌트 거부"""
    # 테넌트 조회
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="테넌트를 찾을 수 없습니다"
        )
    
    # 거부 이메일 발송
    if tenant.email:
        # TODO: 거부 이메일 템플릿 생성 및 발송
        # email_service.set_rejection_email(
        #     receiver_email=tenant.email,
        #     reason=rejection_data.reason
        # ).send()
        pass
    
    # 테넌트 삭제 (또는 거부 상태로 변경)
    # 여기서는 삭제하지 않고 그대로 두되, is_active=False 유지
    
    return {
        "message": "테넌트 등록이 거부되었습니다",
        "tenant_id": tenant_id,
        "reason": rejection_data.reason,
        "rejected_at": datetime.now()
    }
