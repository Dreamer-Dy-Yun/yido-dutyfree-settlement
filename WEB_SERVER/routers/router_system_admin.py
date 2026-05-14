###########################################
# Module name : router_system_admin.py
# Module functions : 시스템 어드민 전용 API (서비스 제공사 관리자)
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.24
# Supported by : Cursor AI
# Note : 시스템 어드민 전용 엔드포인트 (테넌트 관리, 통계, 시스템 설정)
############################################

from datetime import datetime
import hashlib
from typing import Any, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import text, select, func, update, delete
import secrets
import string

from WEB_SERVER.auth.dependencies import get_current_superuser
from WEB_SERVER.routers.settings import get_tenant_repository, get_db_manager
from WEB_SERVER.auth import get_password_hash
from WEB_SERVER.services.service_email import email_service, get_db_smtp_email_service
from WEB_SERVER.services.service_tenant_deletion import TenantDeletionService
from CUSTOMIZED.cust_deco_error import handle_http_error
from CUSTOMIZED.cust_logger import logger

from DATABASE import models
from DATABASE.models.tenant_model import UserRole, User
from DATABASE.models.public_model import (
    ServiceAccount,
    ServiceAccountRole,
    LLM_API_Key,
    Prompt,
)
from DATABASE.repositories.authorities import TenantRepository
from DATABASE.dbms import DBManager
import pandas as pd
import os

router = APIRouter(prefix="/api/system-admin", tags=["시스템 어드민"])


# ============================================================================
# 요청/응답 스키마
# ============================================================================

class TenantRejectionRequest(BaseModel):
    reason: str


class TenantDeletionRequest(BaseModel):
    reason: str


class TenantUpdateRequest(BaseModel):
    name: str | None = None
    alias: str | None = None
    country_code: str | None = None
    contact: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    is_active: bool | None = None


class SystemStatsResponse(BaseModel):
    total_tenants: int
    active_tenants: int
    pending_tenants: int
    total_service_accounts: int
    active_service_accounts: int
    has_smtp_account: bool  # SMTP 송신 계정 존재 여부


class ServiceAccountCreateRequest(BaseModel):
    alias: str | None = None
    e_mail: EmailStr
    password: str
    role: str  # ServiceAccountRole enum value
    description: str | None = None
    is_active: bool = True


class ServiceAccountUpdateRequest(BaseModel):
    alias: str | None = None
    e_mail: EmailStr | None = None
    password: str | None = None
    role: str | None = None
    description: str | None = None
    is_active: bool | None = None


class LLMApiKeyCreateRequest(BaseModel):
    """public.llm_api_key — purpose는 NOT NULL, 클라이언트가 반드시 전달 (빈 값은 422)."""

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


# ============================================================================
# 대시보드 및 통계
# ============================================================================

@router.get("/dashboard/stats", summary="시스템 통계 조회", description="전체 시스템 통계를 조회합니다.")
@handle_http_error
async def get_system_stats(
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: DBManager = Depends(get_db_manager),
):
    """시스템 전체 통계 조회"""
    schemas = ["public"]
    
    # 테넌트 통계
    all_tenants = await tenant_repo.get_all()
    active_tenants = await tenant_repo.get_all(is_active=True)
    pending_tenants = await tenant_repo.get_all(is_active=False)
    
    # 서비스 어카운트 통계
    stmt_total = select(func.count(ServiceAccount.id))
    result_total = await db.execute_query(stmt_total, schemas=schemas)
    total_service_accounts = result_total.scalar() or 0
    
    stmt_active = select(func.count(ServiceAccount.id)).where(ServiceAccount.is_active == True)
    result_active = await db.execute_query(stmt_active, schemas=schemas)
    active_service_accounts = result_active.scalar() or 0
    
    # SMTP 송신 계정 존재 여부 확인
    stmt = select(ServiceAccount).where(
        ServiceAccount.role == ServiceAccountRole.SMTP_SENDER.value,
        ServiceAccount.is_active == True,
    ).limit(1)
    result = await db.execute_query(stmt, schemas=schemas)
    has_smtp_account = result.scalar_one_or_none() is not None
    
    return SystemStatsResponse(
        total_tenants=len(all_tenants),
        active_tenants=len(active_tenants),
        pending_tenants=len(pending_tenants),
        total_service_accounts=total_service_accounts,
        active_service_accounts=active_service_accounts,
        has_smtp_account=has_smtp_account,
    )


# ============================================================================
# 테넌트 관리
# ============================================================================

@router.get("/tenants", summary="테넌트 목록 조회", description="모든 테넌트 목록을 조회합니다.")
@handle_http_error
async def get_tenants(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 레코드 수"),
    is_active: bool | None = Query(None, description="활성화 여부 필터"),
    search: str | None = Query(None, description="검색어 (회사명, 사업자번호)"),
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """테넌트 목록 조회"""
    tenants = await tenant_repo.get_all(skip=skip, limit=limit, is_active=is_active)
    
    # 검색어 필터링 (간단한 구현)
    if search:
        search_lower = search.lower()
        tenants = [
            t for t in tenants
            if search_lower in t.get("name", "").lower()
            or search_lower in t.get("business_no", "").lower()
        ]
    
    return {
        "tenants": tenants,
        "total": len(tenants),
        "skip": skip,
        "limit": limit,
    }


@router.get("/tenants/{tenant_id}", summary="테넌트 상세 조회", description="특정 테넌트의 상세 정보를 조회합니다.")
@handle_http_error
async def get_tenant_detail(
    tenant_id: int,
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """테넌트 상세 조회"""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="테넌트를 찾을 수 없습니다"
        )
    
    # ORM 객체를 dict로 변환
    tenant_dict = tenant.to_dict()
    
    # datetime 필드를 isoformat 문자열로 변환하고 필드명 변경
    tenant_dict["created_at"] = tenant_dict.pop("db_created_at").isoformat() if tenant_dict.get("db_created_at") else None
    tenant_dict["updated_at"] = tenant_dict.pop("db_updated_at").isoformat() if tenant_dict.get("db_updated_at") else None
    
    return tenant_dict


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
        "total": len(tenants),
        "skip": skip,
        "limit": limit,
    }


@router.post("/tenants/{tenant_id}/approve", summary="테넌트 승인", description="테넌트를 승인하고 스키마를 생성합니다.")
@handle_http_error
async def approve_tenant(
    tenant_id: int,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    """테넌트 승인 및 스키마 생성"""
    # DB 변경 단계는 하나의 트랜잭션으로 묶는다.
    async with db.open_session(schemas=["public"]) as session:
        tenant_stmt = (
            select(models.Tenant)
            .where(models.Tenant.id == tenant_id)
            .with_for_update()
        )
        tenant_result = await session.execute(tenant_stmt)
        tenant = tenant_result.scalar_one_or_none()
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

        admin_email = tenant.email
        if not admin_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="관리자 이메일이 등록되지 않았습니다"
            )

        schema_name = tenant.schema_name
        tenant_name = tenant.name
        business_no = tenant.business_no

        # 임시 패스워드 생성 (12자리, 영문+숫자+특수문자)
        temp_password = "".join(
            secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*")
            for _ in range(12)
        )
        hashed_password = get_password_hash(temp_password)

        # 1) 스키마/테이블 생성
        await session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        await session.execute(text(f'SET search_path TO "{schema_name}", "public"'))
        conn = await session.connection()
        await conn.run_sync(models.BaseModel.metadata.create_all)

        # 2) 테넌트 관리자 계정 생성
        admin_user_df = pd.DataFrame([{
            "name": tenant_name,  # 임시로 회사명 사용
            "e_mail": admin_email,
            "password": hashed_password,
            "role": UserRole.ADMIN.value,
            "is_active": True,
        }])
        await db.upsert_batch(table=User, data=admin_user_df, session=session)

        # 3) 승인 상태 업데이트
        await session.execute(
            update(models.Tenant)
            .where(models.Tenant.id == tenant_id)
            .values(is_db_built=True, is_active=True)
        )
        await session.flush()

    # 트랜잭션 커밋 이후에 메일 발송
    app_url = os.getenv("APP_URL", "http://localhost:5173")
    login_url = f"{app_url}/login"
    mail_sent = True
    try:
        smtp_service = await get_db_smtp_email_service(db) or email_service
        smtp_service.set_company_approval_email(
            receiver_email=admin_email,
            company_name=tenant_name,
            login_id=admin_email,
            login_url=login_url,
            temp_password=temp_password,
            business_no=business_no,
        ).send(
            log_success=f"테넌트 승인 이메일 발송 완료: {admin_email}",
            log_error=f"테넌트 승인 이메일 발송 실패: {admin_email}",
        )
    except Exception:
        mail_sent = False
        logger.exception(f"테넌트 승인 완료 후 메일 발송 실패: tenant_id={tenant_id}, email={admin_email}")

    return {
        "message": "테넌트가 승인되었습니다" if mail_sent else "테넌트는 승인되었으나 승인 메일 발송에 실패했습니다",
        "tenant_id": tenant_id,
        "schema_name": schema_name,
        "admin_email": admin_email,
        "temp_password": temp_password,  # 실제로는 메일로만 전송해야 함
        "mail_sent": mail_sent,
        "approved_at": datetime.now().isoformat(),
        "approved_by": current_user.e_mail,
    }


@router.post("/tenants/{tenant_id}/reject", summary="테넌트 거부", description="테넌트 등록을 거부하고 삭제합니다.")
@handle_http_error
async def reject_tenant(
    tenant_id: int,
    rejection_data: TenantRejectionRequest,
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: DBManager = Depends(get_db_manager),
):
    """테넌트 거부 및 삭제"""
    schemas = ["public"]
    
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
            detail="이미 승인된 테넌트는 거부할 수 없습니다"
        )
    
    # 거부 이메일 발송
    if tenant.email:
        smtp_service = await get_db_smtp_email_service(db) or email_service
        smtp_service.set_company_rejection_email(
            receiver_email=tenant.email,
            company_name=tenant.name,
            reason=rejection_data.reason,
            business_no=tenant.business_no,
        ).send(
            log_success=f"테넌트 거부 이메일 발송 완료: {tenant.email}",
            log_error=f"테넌트 거부 이메일 발송 실패: {tenant.email}",
        )
    
    # 거부 시 테넌트 실제 삭제
    stmt = delete(models.Tenant).where(models.Tenant.id == tenant_id)
    await db.execute_query(stmt, schemas=schemas)
    
    return {
        "message": "테넌트 등록이 거부되어 삭제되었습니다",
        "tenant_id": tenant_id,
        "reason": rejection_data.reason,
        "rejected_at": datetime.now().isoformat(),
        "rejected_by": current_user.e_mail,
    }


@router.put("/tenants/{tenant_id}", summary="테넌트 정보 수정", description="테넌트 정보를 수정합니다.")
@handle_http_error
async def update_tenant(
    tenant_id: int,
    update_data: TenantUpdateRequest,
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """테넌트 정보 수정"""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="테넌트를 찾을 수 없습니다"
        )
    
    # 업데이트할 데이터만 필터링
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 데이터가 없습니다"
        )
    
    await tenant_repo.update(tenant_id, update_dict)
    
    # 수정된 테넌트 조회
    updated_tenant = await tenant_repo.get_by_id(tenant_id)
    
    return {
        "message": "테넌트 정보가 수정되었습니다",
        "tenant": {
            "id": updated_tenant.id,
            "name": updated_tenant.name,
            "alias": updated_tenant.alias,
            "business_no": updated_tenant.business_no,
            "contact": updated_tenant.contact,
            "email": updated_tenant.email,
            "address": updated_tenant.address,
            "is_active": updated_tenant.is_active,
        },
        "updated_at": datetime.now().isoformat(),
        "updated_by": current_user.e_mail,
    }


@router.post("/tenants/{tenant_id}/activate", summary="테넌트 활성화", description="테넌트를 활성화합니다.")
@handle_http_error
async def activate_tenant(
    tenant_id: int,
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """테넌트 활성화"""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="테넌트를 찾을 수 없습니다"
        )
    
    if tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 활성화된 테넌트입니다"
        )
    
    # 활성화
    await tenant_repo.update(tenant_id, {"is_active": True})
    
    return {
        "message": "테넌트가 활성화되었습니다",
        "tenant_id": tenant_id,
        "activated_at": datetime.now().isoformat(),
        "activated_by": current_user.e_mail,
    }


@router.post("/tenants/{tenant_id}/deactivate", summary="테넌트 비활성화", description="테넌트를 비활성화합니다. (스키마 및 데이터는 유지)")
@handle_http_error
async def deactivate_tenant(
    tenant_id: int,
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """테넌트 비활성화 (스키마 및 데이터 유지)"""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="테넌트를 찾을 수 없습니다"
        )
    
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 비활성화된 테넌트입니다"
        )
    
    # 비활성화
    await tenant_repo.update(tenant_id, {"is_active": False})
    
    return {
        "message": "테넌트가 비활성화되었습니다",
        "tenant_id": tenant_id,
        "deactivated_at": datetime.now().isoformat(),
        "deactivated_by": current_user.e_mail,
    }


@router.delete("/tenants/{tenant_id}", summary="테넌트 삭제", description="테넌트를 완전히 삭제합니다. (스키마/DB 및 이미지/ZIP 포함 물리 파일 삭제)")
@handle_http_error
async def delete_tenant(
    tenant_id: int,
    deletion_data: TenantDeletionRequest = Body(...),
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: DBManager = Depends(get_db_manager),
):
    """테넌트 완전 삭제 (스키마 및 모든 데이터 삭제)"""
    schemas = ["public"]
    
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="테넌트를 찾을 수 없습니다"
        )
    
    schema_name = tenant.schema_name
    
    # 삭제 이메일 발송 (스키마 삭제 전에 발송)
    if tenant.email:
        smtp_service = await get_db_smtp_email_service(db) or email_service
        smtp_service.set_company_deletion_email(
            receiver_email=tenant.email,
            company_name=tenant.name,
            reason=deletion_data.reason,
            business_no=tenant.business_no,
        ).send(
            log_success=f"테넌트 삭제 이메일 발송 완료: {tenant.email}",
            log_error=f"테넌트 삭제 이메일 발송 실패: {tenant.email}",
        )

    # 0. 테넌트 물리 폴더(이미지/ZIP 포함) 삭제
    #    DB 스키마 drop 전에 삭제해야 "물리 데이터 잔존" 문제를 줄일 수 있습니다.
    await TenantDeletionService.delete_tenant_files(tenant)
    
    # 1. 테넌트 스키마 및 모든 테이블 삭제 (CASCADE로 스키마 삭제 시 모든 테이블도 함께 삭제됨)
    if schema_name:
        # 스키마 삭제 (CASCADE 옵션으로 모든 테이블도 함께 삭제)
        schema_quoted = f'"{schema_name}"'
        await db.execute_query(text(f'DROP SCHEMA IF EXISTS {schema_quoted} CASCADE'), schemas=schemas)
        logger.info(f"테넌트 스키마 '{schema_name}' 및 모든 테이블이 삭제되었습니다")
    
    # 3. public 스키마의 tenant 레코드 삭제
    stmt = delete(models.Tenant).where(models.Tenant.id == tenant_id)
    await db.execute_query(stmt, schemas=schemas)
    
    return {
        "message": "테넌트가 완전히 삭제되었습니다",
        "tenant_id": tenant_id,
        "schema_name": schema_name,
        "deleted_at": datetime.now().isoformat(),
        "deleted_by": current_user.e_mail,
    }


# ============================================================================
# 서비스 어카운트 관리
# ============================================================================

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
    """서비스 어카운트 목록 조회"""
    schemas = ["public"]
    
    stmt = select(ServiceAccount)
    if role:
        stmt = stmt.where(ServiceAccount.role == role)
    if is_active is not None:
        stmt = stmt.where(ServiceAccount.is_active == is_active)
    stmt = stmt.offset(skip).limit(limit)
    
    result = await db.execute_query(stmt, schemas=schemas)
    accounts = result.scalars().all()
    
    accounts_list = []
    for account in accounts:
        account_dict = account.to_dict()
        # password는 보안상 제외
        account_dict.pop("password", None)
        # datetime 필드 변환
        db_created_at = account_dict.pop("db_created_at", None)
        db_updated_at = account_dict.pop("db_updated_at", None)
        account_dict["created_at"] = db_created_at.isoformat() if db_created_at else None
        account_dict["updated_at"] = db_updated_at.isoformat() if db_updated_at else None
        accounts_list.append(account_dict)
    
    return {
        "service_accounts": accounts_list,
        "total": len(accounts_list),
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
    """서비스 어카운트 상세 조회"""
    schemas = ["public"]
    
    stmt = select(ServiceAccount).where(ServiceAccount.id == account_id)
    result = await db.execute_query(stmt, schemas=schemas)
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="서비스 어카운트를 찾을 수 없습니다"
        )
    
    account_dict = account.to_dict()
    # datetime 필드 변환
    db_created_at = account_dict.pop("db_created_at", None)
    db_updated_at = account_dict.pop("db_updated_at", None)
    account_dict["created_at"] = db_created_at.isoformat() if db_created_at else None
    account_dict["updated_at"] = db_updated_at.isoformat() if db_updated_at else None
    
    return account_dict


@router.post("/service-accounts", summary="서비스 어카운트 생성", description="새로운 서비스 어카운트를 생성합니다.")
@handle_http_error
async def create_service_account(
    account_data: ServiceAccountCreateRequest,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    """서비스 어카운트 생성"""
    schemas = ["public"]
    
    # 역할 검증
    try:
        role_enum = ServiceAccountRole(account_data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"유효하지 않은 역할입니다: {account_data.role}"
        )
    
    # 이메일 중복 확인
    stmt = select(ServiceAccount).where(ServiceAccount.e_mail == account_data.e_mail)
    result = await db.execute_query(stmt, schemas=schemas)
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 이메일입니다"
        )
    
    # 서비스 어카운트 생성
    account_df = pd.DataFrame([{
        "alias": account_data.alias,
        "e_mail": account_data.e_mail,
        "password": account_data.password,  # 평문 저장
        "role": str(role_enum.value),  # 명시적으로 문자열로 변환
        "description": account_data.description,
        "is_active": account_data.is_active,
    }])
    
    await db.upsert_batch(table=ServiceAccount, data=account_df, schemas=schemas)
    
    # 생성된 계정 조회
    stmt = select(ServiceAccount).where(ServiceAccount.e_mail == account_data.e_mail)
    result = await db.execute_query(stmt, schemas=schemas)
    created_account = result.scalar_one()
    
    account_dict = created_account.to_dict()
    # password는 보안상 제외
    account_dict.pop("password", None)
    # datetime 필드 변환
    db_created_at = account_dict.pop("db_created_at", None)
    db_updated_at = account_dict.pop("db_updated_at", None)
    account_dict["created_at"] = db_created_at.isoformat() if db_created_at else None
    account_dict["updated_at"] = db_updated_at.isoformat() if db_updated_at else None
    
    return {
        "message": "서비스 어카운트가 등록되었습니다",
        "service_account": account_dict,
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
    """서비스 어카운트 수정"""
    schemas = ["public"]
    
    # 계정 조회
    stmt = select(ServiceAccount).where(ServiceAccount.id == account_id)
    result = await db.execute_query(stmt, schemas=schemas)
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="서비스 어카운트를 찾을 수 없습니다"
        )
    
    # 업데이트할 데이터 준비
    update_dict = {}
    if update_data.alias is not None:
        update_dict["alias"] = update_data.alias
    if update_data.e_mail is not None:
        # 이메일 중복 확인 (자기 자신 제외)
        stmt = select(ServiceAccount).where(
            ServiceAccount.e_mail == update_data.e_mail,
            ServiceAccount.id != account_id
        )
        result = await db.execute_query(stmt, schemas=schemas)
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 존재하는 이메일입니다"
            )
        update_dict["e_mail"] = update_data.e_mail
    if update_data.password is not None:
        update_dict["password"] = update_data.password
    if update_data.role is not None:
        try:
            role_enum = ServiceAccountRole(update_data.role)
            update_dict["role"] = str(role_enum.value)  # 명시적으로 문자열로 변환
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"유효하지 않은 역할입니다: {update_data.role}"
            )
    if update_data.description is not None:
        update_dict["description"] = update_data.description
    if update_data.is_active is not None:
        update_dict["is_active"] = update_data.is_active
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 데이터가 없습니다"
        )
    
    # 업데이트 실행
    stmt = update(ServiceAccount).where(ServiceAccount.id == account_id).values(**update_dict)
    await db.execute_query(stmt, schemas=schemas)
    
    # 수정된 계정 조회
    stmt = select(ServiceAccount).where(ServiceAccount.id == account_id)
    result = await db.execute_query(stmt, schemas=schemas)
    updated_account = result.scalar_one()
    
    account_dict = updated_account.to_dict()
    # password는 보안상 제외
    account_dict.pop("password", None)
    # datetime 필드 변환
    db_created_at = account_dict.pop("db_created_at", None)
    db_updated_at = account_dict.pop("db_updated_at", None)
    account_dict["created_at"] = db_created_at.isoformat() if db_created_at else None
    account_dict["updated_at"] = db_updated_at.isoformat() if db_updated_at else None
    
    return {
        "message": "서비스 어카운트 정보가 수정되었습니다",
        "service_account": account_dict,
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
    """서비스 어카운트 삭제"""
    schemas = ["public"]
    
    # 계정 조회
    stmt = select(ServiceAccount).where(ServiceAccount.id == account_id)
    result = await db.execute_query(stmt, schemas=schemas)
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="서비스 어카운트를 찾을 수 없습니다"
        )
    
    # 실제 삭제 (또는 비활성화)
    # 여기서는 실제 삭제를 수행
    stmt = text(f'DELETE FROM public.service_account WHERE id = :account_id')
    await db.execute_query(stmt, {"account_id": account_id}, schemas=schemas)
    
    return {
        "message": "서비스 어카운트가 삭제되었습니다",
        "account_id": account_id,
        "deleted_at": datetime.now().isoformat(),
        "deleted_by": current_user.e_mail,
    }


# ============================================================================
# LLM API KEY 관리
# ============================================================================

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
        "llm_api_keys": [
            {
                "id": row.id,
                "purpose": row.purpose,
                "llm_provider": row.llm_provider,
                "llm_model": row.llm_model,
                "api_key": LLM_API_Key.mask_api_key(row.api_key),
                "is_active": row.is_active,
                "db_created_at": row.db_created_at,
                "db_updated_at": row.db_updated_at,
            }
            for row in rows
        ],
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
    return row.to_dict()


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
    return {"message": "LLM API Key가 등록되었습니다", "llm_api_key": created.to_dict()}


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
    return {"message": "LLM API Key가 수정되었습니다", "llm_api_key": updated_row.to_dict()}


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


# ============================================================================
# Prompt 관리
# ============================================================================

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
