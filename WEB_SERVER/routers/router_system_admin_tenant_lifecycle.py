###########################################
# Module name : router_system_admin_tenant_lifecycle.py
# Module functions : 시스템 어드민 테넌트 승인/거부/삭제 API
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.24
# Supported by : Cursor AI
# Note : router_system_admin_tenants 하위 lifecycle 라우터
############################################

from datetime import datetime
import os
import secrets
import string

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select, text, update
import pandas as pd

from WEB_SERVER.auth import get_password_hash
from WEB_SERVER.auth.dependencies import get_current_superuser
from WEB_SERVER.routers.settings import get_db_manager, get_tenant_repository
from WEB_SERVER.services.service_email import email_service, get_db_smtp_email_service
from WEB_SERVER.services.service_tenant_deletion import TenantDeletionService
from CUSTOMIZED.cust_deco_error import handle_http_error
from CUSTOMIZED.cust_logger import logger

from DATABASE import models
from DATABASE.models.tenant_model import User, UserRole
from DATABASE.repositories.authorities import TenantRepository
from DATABASE.dbms import DBManager

router = APIRouter()


class TenantRejectionRequest(BaseModel):
    reason: str


class TenantDeletionRequest(BaseModel):
    reason: str


@router.post("/tenants/{tenant_id}/approve", summary="테넌트 승인", description="테넌트를 승인하고 스키마를 생성합니다.")
@handle_http_error
async def approve_tenant(
    tenant_id: int,
    current_user: models.User = Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    """테넌트 승인 및 스키마 생성"""
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

        temp_password = "".join(
            secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*")
            for _ in range(12)
        )
        hashed_password = get_password_hash(temp_password)

        await session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        await session.execute(text(f'SET search_path TO "{schema_name}", "public"'))
        conn = await session.connection()
        await conn.run_sync(models.BaseModel.metadata.create_all)

        admin_user_df = pd.DataFrame([{
            "name": tenant_name,
            "e_mail": admin_email,
            "password": hashed_password,
            "role": UserRole.ADMIN.value,
            "is_active": True,
        }])
        await db.upsert_batch(table=User, data=admin_user_df, session=session)

        await session.execute(
            update(models.Tenant)
            .where(models.Tenant.id == tenant_id)
            .values(is_db_built=True, is_active=True)
        )
        await session.flush()

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
        "temp_password": temp_password,
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

    stmt = delete(models.Tenant).where(models.Tenant.id == tenant_id)
    await db.execute_query(stmt, schemas=schemas)

    return {
        "message": "테넌트 등록이 거부되어 삭제되었습니다",
        "tenant_id": tenant_id,
        "reason": rejection_data.reason,
        "rejected_at": datetime.now().isoformat(),
        "rejected_by": current_user.e_mail,
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

    await TenantDeletionService.delete_tenant_files(tenant)

    if schema_name:
        schema_quoted = f'"{schema_name}"'
        await db.execute_query(text(f'DROP SCHEMA IF EXISTS {schema_quoted} CASCADE'), schemas=schemas)
        logger.info(f"테넌트 스키마 '{schema_name}' 및 모든 테이블이 삭제되었습니다")

    stmt = delete(models.Tenant).where(models.Tenant.id == tenant_id)
    await db.execute_query(stmt, schemas=schemas)

    return {
        "message": "테넌트가 완전히 삭제되었습니다",
        "tenant_id": tenant_id,
        "schema_name": schema_name,
        "deleted_at": datetime.now().isoformat(),
        "deleted_by": current_user.e_mail,
    }
