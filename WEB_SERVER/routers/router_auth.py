###########################################
# Module name : router_auth.py
# Module functions : 사용자 인증 관련 엔드포인트
#                   회원가입, 로그인, 로그아웃, 토큰 갱신
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Supported by : Chat GPT-4o / Cursor AI
# Note : 
############################################

import os
from fastapi import APIRouter, Depends, HTTPException, status, Body, Request, Query
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import timedelta
from DATABASE.repositories.authorities import TenantRepository
from WEB_SERVER.routers.settings import get_tenant_repository, get_db_manager
from DATABASE.dbms import DBManager
from WEB_SERVER.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    oauth2_scheme
)
from WEB_SERVER.auth.dependencies import get_current_superuser
from WEB_SERVER.auth.redis_session import session_manager
from WEB_SERVER.auth.jwt import decode_token
from DATABASE import models
from sqlalchemy import select, update
from CUSTOMIZED.cust_deco_error import handle_http_error

router = APIRouter(prefix="/api/auth", tags=["인증"])


# 요청/응답 스키마
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_id: int  # 회사 선택 ID


class SystemAdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    e_mail: str
    role: str
    is_active: bool
    department: str | None = None
    contact: str | None = None

    class Config:
        from_attributes = True


class VerifyPasswordRequest(BaseModel):
    """비밀번호 확인 (정보 수정 전용, 테넌트 사용자)"""
    password: str


class UserProfileUpdateRequest(BaseModel):
    """테넌트 사용자 본인 정보 수정 (비밀번호 확인 필요)"""
    current_password: str
    name: str | None = None
    department: str | None = None
    contact: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


# 로그인
@router.post("/login", summary="로그인", description="회사 선택 후 사용자 인증하여 JWT 토큰을 발급합니다.", response_model=Token)
@handle_http_error
async def login(
    login_data: LoginRequest,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: DBManager = Depends(get_db_manager),
):
    """회사 선택 후 로그인"""
    # 테넌트 조회 및 활성화 확인
    tenant = await tenant_repo.get_by_id(login_data.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="승인되지 않은 회사입니다"
        )
    
    # 테넌트 스키마로 전환
    await db.set_schemas([tenant.schema_name, "public"])
    
    # 테넌트 스키마에서 사용자 조회
    stmt = select(models.User).where(models.User.e_mail == login_data.email)
    result = await db.execute_query(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 비밀번호 확인
    if not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 활성화 여부 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )
    
    # 사용자별 토큰 유효기간 조회
    user_token_expire_minutes = session_manager.get_user_token_expire_minutes(
        user_id=user.id,
        default=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    # 액세스 토큰 생성 (이메일, 테넌트 정보 포함)
    access_token_expires = timedelta(minutes=user_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": user.e_mail,
            "tenant_id": tenant.id,
            "tenant_schema": tenant.schema_name,
            "user_id": user.id,
        },
        expires_delta=access_token_expires
    )
    
    # Redis에 세션 저장
    expires_in_seconds = user_token_expire_minutes * 60
    session_manager.create_session(
        token=access_token,
        user_id=user.id,
        email=user.e_mail,
        expires_in=expires_in_seconds
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# 시스템 어드민 로그인
@router.post("/system-admin/login", summary="시스템 어드민 로그인", description="서비스 제공사 관리자 로그인 (SystemAdmin 인증)", response_model=Token)
@handle_http_error
async def system_admin_login(
    login_data: SystemAdminLoginRequest,
    db: DBManager = Depends(get_db_manager),
):
    """시스템 어드민 로그인 (SystemAdmin 인증)"""
    from DATABASE.models.public_model import SystemAdmin
    
    # public 스키마로 전환
    await db.set_schemas(["public"])
    
    # SystemAdmin에서 사용자 조회
    stmt = select(SystemAdmin).where(SystemAdmin.e_mail == login_data.email)
    result = await db.execute_query(stmt)
    system_admin = result.scalar_one_or_none()
    
    if not system_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 비밀번호 확인 (해시된 패스워드 검증)
    if not verify_password(login_data.password, system_admin.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 활성화 여부 확인
    if not system_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )
    
    # 액세스 토큰 생성 (시스템 어드민 정보 포함)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": system_admin.e_mail,
            "is_superuser": True,
            "role": "system_admin",
            "user_id": system_admin.id,
            # 시스템 어드민은 tenant_id가 없음
            "tenant_id": None,
            "tenant_schema": None,
        },
        expires_delta=access_token_expires
    )
    
    # Redis에 세션 저장
    expires_in_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    session_manager.create_session(
        token=access_token,
        user_id=system_admin.id,
        email=system_admin.e_mail,
        expires_in=expires_in_seconds
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# 현재 사용자 정보 조회
@router.get("/me", summary="현재 사용자 정보", description="현재 로그인한 사용자의 정보를 조회합니다.", response_model=UserResponse)
@handle_http_error
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user),
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "e_mail": current_user.e_mail,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        "is_active": current_user.is_active,
        "department": getattr(current_user, "department", None),
        "contact": getattr(current_user, "contact", None),
    }


# 비밀번호 확인 (테넌트·시스템 어드민 공용, 토큰으로 구분)
@router.post("/verify-password", summary="비밀번호 확인", description="정보 수정 전 비밀번호를 확인합니다. (테넌트/시스템 어드민 공용)")
@handle_http_error
async def verify_password_me(
    body: VerifyPasswordRequest,
    token: str = Depends(oauth2_scheme),
    db: DBManager = Depends(get_db_manager),
):
    if not session_manager.is_session_valid(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰이 만료되었습니다. 다시 로그인 해 주세요.")
    payload = decode_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")
    if payload.get("is_superuser"):
        from DATABASE.models.public_model import SystemAdmin
        await db.set_schemas(["public"])
        stmt = select(SystemAdmin).where(SystemAdmin.id == user_id)
        row = await db.execute_query(stmt)
        user = row.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="비밀번호가 일치하지 않습니다.")
    else:
        tenant_schema = payload.get("tenant_schema")
        if not tenant_schema:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")
        await db.set_schemas([tenant_schema, "public"])
        stmt = select(models.User).where(models.User.id == user_id)
        row = await db.execute_query(stmt)
        user = row.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="비밀번호가 일치하지 않습니다.")
    if not verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="비밀번호가 일치하지 않습니다.")
    return {"message": "확인되었습니다."}


# 테넌트 사용자 본인 정보 수정 (비밀번호 확인 필요)
@router.put("/me", summary="본인 정보 수정", description="비밀번호 확인 후 이름/부서/연락처를 수정합니다.")
@handle_http_error
async def update_user_me(
    body: UserProfileUpdateRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: DBManager = Depends(get_db_manager),
):
    if not verify_password(body.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비밀번호가 일치하지 않습니다.",
        )
    update_data = {}
    if body.name is not None:
        update_data["name"] = body.name
    if body.department is not None:
        update_data["department"] = body.department
    if body.contact is not None:
        update_data["contact"] = body.contact
    if not update_data:
        return {"message": "변경할 항목이 없습니다."}
    stmt = update(models.User).where(models.User.id == current_user.id).values(**update_data)
    await db.execute_query(stmt)
    return {"message": "정보가 수정되었습니다."}


# 토큰 갱신
@router.post("/refresh", summary="토큰 갱신", description="액세스 토큰을 갱신합니다.", response_model=Token)
@handle_http_error
async def refresh_token(
    current_user: models.User = Depends(get_current_active_user),
    old_token: str = Depends(oauth2_scheme),
    db: DBManager = Depends(get_db_manager),
):
    """토큰 갱신"""
    # 기존 토큰에서 테넌트 정보 추출
    payload = decode_token(old_token)
    tenant_id = payload.get("tenant_id")
    tenant_schema = payload.get("tenant_schema")
    
    if not tenant_id or not tenant_schema:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다"
        )
    
    # 기존 토큰 삭제
    session_manager.delete_session(old_token)
    
    # 사용자별 토큰 유효기간 조회
    user_token_expire_minutes = session_manager.get_user_token_expire_minutes(
        user_id=current_user.id,
        default=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    # 새 토큰 생성 (테넌트 정보 포함)
    access_token_expires = timedelta(minutes=user_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": current_user.e_mail,
            "tenant_id": tenant_id,
            "tenant_schema": tenant_schema,
            "user_id": current_user.id,
        },
        expires_delta=access_token_expires
    )
    
    # 새 토큰을 Redis에 저장
    expires_in_seconds = user_token_expire_minutes * 60
    session_manager.create_session(
        token=access_token,
        user_id=current_user.id,
        email=current_user.e_mail,
        expires_in=expires_in_seconds
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# 비밀번호 변경 (테넌트·시스템 어드민 공용, 토큰으로 구분)
@router.post("/change-password", summary="비밀번호 변경", description="현재 사용자의 비밀번호를 변경합니다. (테넌트/시스템 어드민 공용)")
@handle_http_error
async def change_password(
    old_password: str = Body(None, description="현재 비밀번호 (임시 패스워드 변경 시 생략 가능)"),
    new_password: str = Body(...),
    is_temp_password: bool = Body(False, description="임시 패스워드 변경 여부"),
    token: str = Depends(oauth2_scheme),
    db: DBManager = Depends(get_db_manager),
):
    """비밀번호 변경 (임시 패스워드 변경 포함). 토큰이 시스템 어드민이면 SystemAdmin, 아니면 테넌트 User 대상."""
    if not session_manager.is_session_valid(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰이 만료되었습니다. 다시 로그인 해 주세요.")
    payload = decode_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")
    if payload.get("is_superuser"):
        from DATABASE.models.public_model import SystemAdmin
        await db.set_schemas(["public"])
        stmt = select(SystemAdmin).where(SystemAdmin.id == user_id)
        row = await db.execute_query(stmt)
        current_user = row.scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자를 찾을 수 없습니다.")
        if not is_temp_password:
            if not old_password:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="현재 비밀번호를 입력해주세요")
            if not verify_password(old_password, current_user.password):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="현재 비밀번호가 올바르지 않습니다")
        hashed_password = get_password_hash(new_password)
        stmt = update(SystemAdmin).where(SystemAdmin.id == current_user.id).values(password=hashed_password)
        await db.execute_query(stmt)
    else:
        tenant_schema = payload.get("tenant_schema")
        if not tenant_schema:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")
        await db.set_schemas([tenant_schema, "public"])
        stmt = select(models.User).where(models.User.id == user_id)
        row = await db.execute_query(stmt)
        current_user = row.scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자를 찾을 수 없습니다.")
        if not is_temp_password:
            if not old_password:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="현재 비밀번호를 입력해주세요")
            if not verify_password(old_password, current_user.password):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="현재 비밀번호가 올바르지 않습니다")
        hashed_password = get_password_hash(new_password)
        stmt = update(models.User).where(models.User.id == current_user.id).values(password=hashed_password)
        await db.execute_query(stmt)
    return {"message": "비밀번호가 변경되었습니다"}


# 로그아웃
@router.post("/logout", summary="로그아웃", description="현재 사용자를 로그아웃합니다.")
@handle_http_error
async def logout(
    current_user: models.User = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme),
):
    """로그아웃 - Redis에서 세션 제거"""
    # Redis에서 세션 삭제
    session_manager.delete_session(token)
    
    return {"message": "로그아웃되었습니다"}


# 시스템 어드민 현재 사용자 정보 조회
@router.get("/system-admin/me", summary="시스템 어드민 현재 사용자 정보", description="현재 로그인한 시스템 관리자의 정보를 조회합니다.")
@handle_http_error
async def read_system_admin_me(
    current_superuser = Depends(get_current_superuser),
):
    """시스템 어드민 현재 사용자 정보 조회"""
    return {
        "id": current_superuser.id,
        "name": current_superuser.name,
        "alias": current_superuser.alias,
        "e_mail": current_superuser.e_mail,
        "department": current_superuser.department,
        "contact": current_superuser.contact,
        "is_active": current_superuser.is_active,
    }


class SystemAdminProfileUpdate(BaseModel):
    """시스템 어드민 정보 수정 요청 (비밀번호 확인 후 수정 가능)"""
    current_password: str
    name: str | None = None
    alias: str | None = None
    department: str | None = None
    contact: str | None = None


# 시스템 어드민 정보 수정 (비밀번호 확인 필요)
@router.put("/system-admin/me", summary="시스템 어드민 정보 수정", description="비밀번호 확인 후 이름/별칭/부서/연락처를 수정합니다.")
@handle_http_error
async def update_system_admin_me(
    body: SystemAdminProfileUpdate,
    current_superuser=Depends(get_current_superuser),
    db: DBManager = Depends(get_db_manager),
):
    """시스템 어드민 정보 수정 (현재 비밀번호 검증 후 수정)"""
    from DATABASE.models.public_model import SystemAdmin

    if not verify_password(body.current_password, current_superuser.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비밀번호가 일치하지 않습니다.",
        )

    update_data = {}
    if body.name is not None:
        update_data["name"] = body.name
    if body.alias is not None:
        update_data["alias"] = body.alias
    if body.department is not None:
        update_data["department"] = body.department
    if body.contact is not None:
        update_data["contact"] = body.contact

    if not update_data:
        return {"message": "변경할 항목이 없습니다."}

    await db.set_schemas(["public"])
    stmt = update(SystemAdmin).where(SystemAdmin.id == current_superuser.id).values(**update_data)
    await db.execute_query(stmt)

    return {"message": "정보가 수정되었습니다."}


# 시스템 어드민 로그아웃
@router.post("/system-admin/logout", summary="시스템 어드민 로그아웃", description="시스템 관리자를 로그아웃합니다.")
@handle_http_error
async def system_admin_logout(
    token: str = Depends(oauth2_scheme),
    current_superuser = Depends(get_current_superuser),
):
    """시스템 어드민 로그아웃 - Redis에서 세션 제거"""
    # Redis에서 세션 삭제
    session_manager.delete_session(token)
    
    return {"message": "로그아웃되었습니다"}


# 모든 기기에서 로그아웃
@router.post("/logout-all", summary="모든 기기 로그아웃", description="현재 사용자의 모든 세션을 종료합니다.")
@handle_http_error
async def logout_all(
    current_user: models.User = Depends(get_current_active_user),
):
    """모든 기기에서 로그아웃 - 사용자의 모든 세션 제거"""
    # 사용자의 모든 세션 삭제
    session_manager.delete_all_user_sessions(current_user.id)
    
    return {"message": "모든 기기에서 로그아웃되었습니다"}


# 토큰 유효기간 설정
@router.post("/token-expire", summary="토큰 유효기간 설정", description="현재 사용자의 토큰 유효기간을 설정합니다.")
@handle_http_error
async def set_token_expire(
    expire_minutes: int = Body(..., ge=1, le=1440, description="토큰 유효기간 (분, 1~1440분)"),
    current_user: models.User = Depends(get_current_active_user),
):
    """토큰 유효기간 설정 (1분 ~ 24시간)"""
    # Redis에 사용자별 설정 저장
    session_manager.set_user_token_expire_minutes(
        user_id=current_user.id,
        expire_minutes=expire_minutes
    )
    
    return {
        "message": f"토큰 유효기간이 {expire_minutes}분으로 설정되었습니다",
        "expire_minutes": expire_minutes
    }


# 토큰 유효기간 조회
@router.get("/token-expire", summary="토큰 유효기간 조회", description="현재 사용자의 토큰 유효기간을 조회합니다.")
@handle_http_error
async def get_token_expire(
    current_user: models.User = Depends(get_current_active_user),
):
    """토큰 유효기간 조회"""
    expire_minutes = session_manager.get_user_token_expire_minutes(
        user_id=current_user.id,
        default=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    return {
        "expire_minutes": expire_minutes,
        "default": ACCESS_TOKEN_EXPIRE_MINUTES
    }


