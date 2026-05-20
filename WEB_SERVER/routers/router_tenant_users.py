###########################################
# Module name : router_tenant_users.py
# Module functions : Tenant user, usage, and tenant-info APIs
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.05.20
# Note : Included by router_tenant.py; do not duplicate the /api/tenant prefix here.
############################################

from datetime import datetime, timedelta
import os
import secrets
import string
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select, update as sql_update, delete as sql_delete
from sqlalchemy.sql import Select

from WEB_SERVER.auth import get_password_hash
from WEB_SERVER.auth.dependencies import get_current_tenant_admin
from WEB_SERVER.routers.settings import get_db_manager
from WEB_SERVER.routers.tenant_helpers import (
    _count_created_rows,
    _created_at_range_conditions,
    _get_current_public_tenant,
    _get_current_tenant_schema_from_user,
    _get_current_tenant_schemas,
    _is_valid_email,
    _tenant_info_response,
)
from WEB_SERVER.routers.tenant_schemas import (
    TenantInfoUpdateRequest,
    UserActivationRequest,
    UserCreateRequest,
    UserUpdateRequest,
)
from WEB_SERVER.services.service_email import email_service, get_db_smtp_email_service
from WEB_SERVER.services.verification_token import verification_token_service
from CUSTOMIZED.cust_deco_error import handle_http_error
from DATABASE import models
from DATABASE.dbms import DBManager
from DATABASE.models.public_model import Tenant as PublicTenant
import pandas as pd

router = APIRouter()


def _user_response(user: models.User) -> dict[str, Any]:
    return {
        "id": user.id,
        "name": user.name,
        "e_mail": user.e_mail,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "department": user.department,
        "contact": user.contact,
        "is_active": user.is_active,
        "created_at": user.db_created_at,
        "updated_at": user.db_updated_at,
    }


async def _get_user_or_404(db: DBManager, schemas: list[str], user_id: int, detail: str = "유저를 찾을 수 없습니다"):
    result = await db.execute_query(select(models.User).where(models.User.id == user_id), schemas=schemas)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return user


def _default_period(start_date: datetime | None, end_date: datetime | None) -> tuple[datetime, datetime]:
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    return start_date, end_date


async def _send_user_deletion_notice(db: DBManager, receiver_email: str, receiver_name: str) -> tuple[bool, str]:
    smtp_service = await get_db_smtp_email_service(db) or email_service
    sender_email = (getattr(smtp_service, "_sender", "") or "").strip()
    smtp_user = (getattr(smtp_service, "_user", "") or "").strip()
    smtp_password = (getattr(smtp_service, "_password", "") or "").strip()
    if not sender_email or not smtp_user or not smtp_password or not _is_valid_email(sender_email):
        return False, "유저 삭제는 완료되었지만 송신자 메일 계정이 유효하지 않아 확인 메일을 발송하지 못했습니다. 시스템 관리자에게 문의해 주세요."
    if not _is_valid_email(receiver_email):
        return False, "유저 삭제는 완료되었지만 수신자 메일 주소가 유효하지 않아 확인 메일을 발송하지 못했습니다."
    mail_sent = smtp_service.set_user_deletion_email(receiver_email=receiver_email, receiver_name=receiver_name).send(
        log_success=f"유저 삭제 확인 이메일 발송 완료: {receiver_email}",
        log_error=f"유저 삭제 확인 이메일 발송 실패: {receiver_email}",
    )
    if mail_sent:
        return True, "유저 삭제가 완료되었고 삭제 확인 메일을 발송했습니다."
    return False, "유저 삭제는 완료되었지만 확인 메일 발송에 실패했습니다."


@router.get("/users", summary="유저 목록 조회", description="테넌트의 모든 유저 목록을 조회합니다.")
@handle_http_error
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: bool | None = Query(None),
    current_user: models.User = Depends(get_current_tenant_admin),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    stmt: Select = select(models.User)
    if is_active is not None:
        stmt = stmt.where(models.User.is_active == is_active)
    result = await db.execute_query(stmt.offset(skip).limit(limit).order_by(models.User.db_created_at.desc()), schemas=schemas)
    return [_user_response(user) for user in result.scalars().all()]


@router.post("/users", summary="유저 추가", description="새로운 유저를 추가합니다.")
@handle_http_error
async def create_user(
    user_data: UserCreateRequest,
    current_user: models.User = Depends(get_current_tenant_admin),
    db: DBManager = Depends(get_db_manager),
):
    schemas = [_get_current_tenant_schema_from_user(current_user)]
    result = await db.execute_query(select(models.User).where(models.User.e_mail == user_data.e_mail), schemas=schemas)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 사용 중인 이메일입니다")
    await db.upsert_batch(table=models.User, data=pd.DataFrame([{
        "name": user_data.name,
        "e_mail": user_data.e_mail,
        "password": get_password_hash(user_data.password),
        "role": user_data.role.value,
        "department": user_data.department,
        "contact": user_data.contact,
        "is_active": False,
    }]), schemas=schemas)
    result = await db.execute_query(select(models.User).where(models.User.e_mail == user_data.e_mail), schemas=schemas)
    created_user = result.scalar_one_or_none()
    if not created_user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="유저 생성 후 조회에 실패했습니다")
    verification_token = verification_token_service.generate_token(user_data.e_mail)
    verification_token_service.save_token(user_data.e_mail, verification_token, created_user.id)
    email_service.set_verification_email(
        receiver_email=user_data.e_mail,
        receiver_name=user_data.name,
        verification_token=verification_token,
        service_url=os.getenv("APP_URL", "http://localhost:5173"),
    ).send(log_success=f"인증 이메일 발송 완료: {user_data.e_mail}", log_error=f"인증 이메일 발송 실패: {user_data.e_mail}")
    return {"message": "유저가 추가되었습니다. 이메일을 확인하여 인증을 완료해주세요.", "user_id": created_user.id, "e_mail": user_data.e_mail}


@router.get("/users/{user_id}", summary="유저 상세 조회", description="특정 유저의 상세 정보를 조회합니다.")
@handle_http_error
async def get_user(user_id: int, current_user: models.User = Depends(get_current_tenant_admin), db: DBManager = Depends(get_db_manager)):
    return _user_response(await _get_user_or_404(db, _get_current_tenant_schemas(current_user), user_id))


@router.put("/users/{user_id}", summary="유저 수정", description="유저 정보를 수정합니다.")
@handle_http_error
async def update_user(user_id: int, user_data: UserUpdateRequest, current_user: models.User = Depends(get_current_tenant_admin), db: DBManager = Depends(get_db_manager)):
    schemas = _get_current_tenant_schemas(current_user)
    await _get_user_or_404(db, schemas, user_id)
    update_data: dict[str, Any] = {}
    for field in ("name", "e_mail", "department", "contact", "is_active"):
        value = getattr(user_data, field)
        if value is not None:
            update_data[field] = value
    if user_data.role is not None:
        update_data["role"] = user_data.role.value
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="수정할 데이터가 없습니다")
    await db.execute_query(sql_update(models.User).where(models.User.id == user_id).values(**update_data), schemas=schemas)
    return {"message": "유저 정보가 수정되었습니다", "user_id": user_id}


@router.patch("/users/{user_id}/activation", summary="유저 활성 상태 변경", description="유저의 활성 상태를 설정합니다.")
@handle_http_error
async def user_activate(user_id: int, activation_data: UserActivationRequest, current_user: models.User = Depends(get_current_tenant_admin), db: DBManager = Depends(get_db_manager)):
    schemas = _get_current_tenant_schemas(current_user)
    user = await _get_user_or_404(db, schemas, user_id)
    if user.id == current_user.id and not activation_data.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="자기 자신은 비활성화할 수 없습니다")
    await db.execute_query(sql_update(models.User).where(models.User.id == user_id).values(is_active=activation_data.is_active), schemas=schemas)
    return {"message": "유저가 활성화되었습니다" if activation_data.is_active else "유저가 비활성화되었습니다", "user_id": user_id, "is_active": activation_data.is_active}


@router.delete("/users/{user_id}", summary="유저 삭제", description="유저를 물리적으로 삭제합니다.")
@handle_http_error
async def delete_user(user_id: int, current_user: models.User = Depends(get_current_tenant_admin), db: DBManager = Depends(get_db_manager)):
    schemas = _get_current_tenant_schemas(current_user)
    user = await _get_user_or_404(db, schemas, user_id)
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="자기 자신은 삭제할 수 없습니다")
    receiver_email = (getattr(user, "e_mail", "") or "").strip()
    receiver_name = (getattr(user, "name", "") or "").strip() or receiver_email
    await db.execute_query(sql_delete(models.User).where(models.User.id == user_id), schemas=schemas)
    mail_sent, mail_notice = await _send_user_deletion_notice(db, receiver_email, receiver_name)
    return {"message": "유저가 삭제되었습니다", "user_id": user_id, "mail_sent": mail_sent, "mail_notice": mail_notice}


@router.post("/users/{user_id}/reset-password", summary="비밀번호 재설정", description="유저의 비밀번호를 재설정합니다.")
@handle_http_error
async def reset_password(user_id: int, current_user: models.User = Depends(get_current_tenant_admin), db: DBManager = Depends(get_db_manager)):
    schemas = _get_current_tenant_schemas(current_user)
    user = await _get_user_or_404(db, schemas, user_id)
    temp_password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    await db.execute_query(sql_update(models.User).where(models.User.id == user_id).values(password=get_password_hash(temp_password)), schemas=schemas)
    smtp_service = await get_db_smtp_email_service(db) or email_service
    smtp_service.set_user_temp_password_email(
        receiver_email=user.e_mail,
        receiver_name=getattr(user, "name", None) or user.e_mail,
        temp_password=temp_password,
        login_url=f"{os.getenv('APP_URL', 'http://localhost:5173')}/login",
    ).send(log_success=f"임시 비밀번호 이메일 발송 완료: {user.e_mail}", log_error=f"임시 비밀번호 이메일 발송 실패: {user.e_mail}")
    return {"message": "임시 비밀번호가 등록된 이메일로 발송되었습니다", "user_id": user_id}


@router.get("/usage", summary="전체 사용량 조회", description="테넌트의 전체 사용량을 조회합니다.")
@handle_http_error
async def get_usage(start_date: datetime | None = Query(None, description="시작 날짜"), end_date: datetime | None = Query(None, description="종료 날짜"), current_user: models.User = Depends(get_current_tenant_admin), db: DBManager = Depends(get_db_manager)):
    schemas = _get_current_tenant_schemas(current_user)
    start_date, end_date = _default_period(start_date, end_date)
    usage = {
        "total_images": await _count_created_rows(db, schemas, models.Image, start_date, end_date),
        "total_ocr_passport": await _count_created_rows(db, schemas, models.OcrPassport, start_date, end_date),
        "total_ocr_receipt": await _count_created_rows(db, schemas, models.OcrReceipt, start_date, end_date),
        "total_verified_passport": await _count_created_rows(db, schemas, models.VerifiedPassport, start_date, end_date),
        "total_verified_receipt": await _count_created_rows(db, schemas, models.VerifiedReceipt, start_date, end_date),
        "total_matched": await _count_created_rows(db, schemas, models.Matched, start_date, end_date),
    }
    stmt = select(func.sum(models.LlmUsage.token_total))
    conditions = _created_at_range_conditions(models.LlmUsage, start_date, end_date)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    total_llm_tokens = (await db.execute_query(stmt, schemas=schemas)).scalar() or 0
    return {**usage, "total_llm_tokens": int(total_llm_tokens) if total_llm_tokens else 0, "period_start": start_date, "period_end": end_date}


@router.get("/usage/users/{user_id}/tokens", summary="사용자별 토큰 사용량 조회", description="특정 사용자의 LLM 토큰 사용량을 조회합니다.")
@handle_http_error
async def get_user_token_usage(user_id: int, start_date: datetime | None = Query(None, description="시작 날짜"), end_date: datetime | None = Query(None, description="종료 날짜"), current_user: models.User = Depends(get_current_tenant_admin), db: DBManager = Depends(get_db_manager)):
    schemas = _get_current_tenant_schemas(current_user)
    user = await _get_user_or_404(db, schemas, user_id, detail="사용자를 찾을 수 없습니다")
    start_date, end_date = _default_period(start_date, end_date)
    stmt = select(
        func.sum(models.LlmUsage.token_input).label("token_input"),
        func.sum(models.LlmUsage.token_output).label("token_output"),
        func.sum(models.LlmUsage.token_total).label("token_total"),
        func.count(models.LlmUsage.id).label("usage_count"),
    )
    conditions = _created_at_range_conditions(models.LlmUsage, start_date, end_date)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    row = (await db.execute_query(stmt, schemas=schemas)).first()
    return {
        "user_id": user_id,
        "user_name": user.name,
        "user_email": user.e_mail,
        "token_input": int(row.token_input) if row.token_input else 0,
        "token_output": int(row.token_output) if row.token_output else 0,
        "token_total": int(row.token_total) if row.token_total else 0,
        "usage_count": row.usage_count or 0,
        "period_start": start_date,
        "period_end": end_date,
    }


@router.get("/info", summary="테넌트 정보 조회", description="테넌트 정보를 조회합니다.")
@handle_http_error
async def get_tenant_info(current_user: models.User = Depends(get_current_tenant_admin), db: DBManager = Depends(get_db_manager)):
    return _tenant_info_response(await _get_current_public_tenant(current_user, db))


@router.put("/info", summary="테넌트 정보 수정", description="테넌트 정보를 수정합니다.")
@handle_http_error
async def update_tenant_info(body: TenantInfoUpdateRequest, current_user: models.User = Depends(get_current_tenant_admin), db: DBManager = Depends(get_db_manager)):
    tenant = await _get_current_public_tenant(current_user, db)
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="수정할 데이터가 없습니다.")
    await db.execute_query(sql_update(PublicTenant).where(PublicTenant.id == tenant.id).values(**update_data), schemas=["public"])
    result_after = await db.execute_query(select(PublicTenant).where(PublicTenant.id == tenant.id), schemas=["public"])
    return {"message": "테넌트 정보가 수정되었습니다", "tenant": _tenant_info_response(result_after.scalar_one())}
