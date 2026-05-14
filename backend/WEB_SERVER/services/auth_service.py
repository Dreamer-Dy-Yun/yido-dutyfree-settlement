###########################################
# Module name : auth_service.py
# Module functions : 인증/토큰/프로필 관련 비즈니스 로직
# Written by : Cursor AI (with Yun Dae-young)
# Note :
#   - 라우터(`router_auth.py`)에서 HTTP/의존성만 처리하고
#     실제 비즈니스 로직은 이 모듈로 위임하기 위한 서비스 레이어
############################################

from datetime import timedelta
from typing import Any, Dict

from fastapi import HTTPException, status
from sqlalchemy import select, update

from DATABASE import models
from DATABASE.dbms import DBManager
from DATABASE.repositories.authorities import TenantRepository
from WEB_SERVER.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    oauth2_scheme,
)
from WEB_SERVER.auth.dependencies import get_current_superuser  # type: ignore  # IDE 힌트용
from WEB_SERVER.auth.jwt import decode_token
from WEB_SERVER.auth.redis_session import session_manager


async def login_service(
    *,
    email: str,
    password: str,
    tenant_id: int,
    tenant_repo: TenantRepository,
    db: DBManager,
) -> Dict[str, str]:
    """
    회사(테넌트) 선택 후 로그인 비즈니스 로직.
    """
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다",
        )

    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="승인되지 않은 회사입니다",
        )

    schemas = [tenant.schema_name, "public"]

    stmt = select(models.User).where(models.User.e_mail == email)
    result = await db.execute_query(stmt, schemas=schemas)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다",
        )

    user_token_expire_minutes = session_manager.get_user_token_expire_minutes(
        user_id=user.id,
        default=ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    access_token_expires = timedelta(minutes=user_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": user.e_mail,
            "tenant_id": tenant.id,
            "tenant_schema": tenant.schema_name,
            "user_id": user.id,
        },
        expires_delta=access_token_expires,
    )

    expires_in_seconds = user_token_expire_minutes * 60
    session_manager.create_session(
        token=access_token,
        user_id=user.id,
        email=user.e_mail,
        expires_in=expires_in_seconds,
    )

    return {"access_token": access_token, "token_type": "bearer"}


async def system_admin_login_service(
    *,
    email: str,
    password: str,
    db: DBManager,
) -> Dict[str, str]:
    """
    시스템 어드민 로그인 비즈니스 로직.
    """
    from DATABASE.models.public_model import SystemAdmin

    schemas = ["public"]

    stmt = select(SystemAdmin).where(SystemAdmin.e_mail == email)
    result = await db.execute_query(stmt, schemas=schemas)
    system_admin = result.scalar_one_or_none()

    if not system_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(password, system_admin.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not system_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": system_admin.e_mail,
            "is_superuser": True,
            "role": "system_admin",
            "user_id": system_admin.id,
            "tenant_id": None,
            "tenant_schema": None,
        },
        expires_delta=access_token_expires,
    )

    expires_in_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    session_manager.create_session(
        token=access_token,
        user_id=system_admin.id,
        email=system_admin.e_mail,
        expires_in=expires_in_seconds,
    )

    return {"access_token": access_token, "token_type": "bearer"}


async def verify_password_me_service(
    *,
    plain_password: str,
    token: str,
    db: DBManager,
) -> Dict[str, str]:
    """
    토큰 기반 비밀번호 검증 (테넌트/시스템 어드민 공용).
    """
    if not session_manager.is_session_valid(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었습니다. 다시 로그인 해 주세요.",
        )

    payload = decode_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )

    if payload.get("is_superuser"):
        from DATABASE.models.public_model import SystemAdmin

        schemas = ["public"]
        stmt = select(SystemAdmin).where(SystemAdmin.id == user_id)
        row = await db.execute_query(stmt, schemas=schemas)
        user = row.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="비밀번호가 일치하지 않습니다.",
            )
    else:
        tenant_schema = payload.get("tenant_schema")
        if not tenant_schema:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다.",
            )
        schemas = [tenant_schema, "public"]
        stmt = select(models.User).where(models.User.id == user_id)
        row = await db.execute_query(stmt, schemas=schemas)
        user = row.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="비밀번호가 일치하지 않습니다.",
            )

    if not verify_password(plain_password, user.password):  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비밀번호가 일치하지 않습니다.",
        )

    return {"message": "확인되었습니다."}


async def update_user_me_service(
    *,
    current_password: str,
    update_data: Dict[str, Any],
    current_user: models.User,
    db: DBManager,
) -> Dict[str, str]:
    """
    테넌트 사용자 본인 정보 수정 로직.
    """
    if not verify_password(current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비밀번호가 일치하지 않습니다.",
        )

    if not update_data:
        return {"message": "변경할 항목이 없습니다."}

    stmt = (
        update(models.User)
        .where(models.User.id == current_user.id)
        .values(**update_data)
    )
    await db.execute_query(stmt)

    return {"message": "정보가 수정되었습니다."}


async def refresh_token_service(
    *,
    current_user: models.User,
    old_token: str,
) -> Dict[str, str]:
    """
    액세스 토큰 갱신 로직.
    DB 접근이 없으므로 DBManager 의존성은 받지 않는다.
    """
    payload = decode_token(old_token)
    tenant_id = payload.get("tenant_id")
    tenant_schema = payload.get("tenant_schema")

    if not tenant_id or not tenant_schema:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
        )

    session_manager.delete_session(old_token)

    user_token_expire_minutes = session_manager.get_user_token_expire_minutes(
        user_id=current_user.id,
        default=ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    access_token_expires = timedelta(minutes=user_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": current_user.e_mail,
            "tenant_id": tenant_id,
            "tenant_schema": tenant_schema,
            "user_id": current_user.id,
        },
        expires_delta=access_token_expires,
    )

    expires_in_seconds = user_token_expire_minutes * 60
    session_manager.create_session(
        token=access_token,
        user_id=current_user.id,
        email=current_user.e_mail,
        expires_in=expires_in_seconds,
    )

    return {"access_token": access_token, "token_type": "bearer"}


async def change_password_service(
    *,
    old_password: str | None,
    new_password: str,
    is_temp_password: bool,
    token: str,
    db: DBManager,
) -> Dict[str, str]:
    """
    비밀번호 변경 (임시 패스워드 포함) 로직.
    """
    if not session_manager.is_session_valid(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었습니다. 다시 로그인 해 주세요.",
        )

    payload = decode_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )

    if payload.get("is_superuser"):
        from DATABASE.models.public_model import SystemAdmin

        schemas = ["public"]
        stmt = select(SystemAdmin).where(SystemAdmin.id == user_id)
        row = await db.execute_query(stmt, schemas=schemas)
        current_user = row.scalar_one_or_none()
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자를 찾을 수 없습니다.",
            )

        if not is_temp_password:
            if not old_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="현재 비밀번호를 입력해주세요",
                )
            if not verify_password(old_password, current_user.password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="현재 비밀번호가 올바르지 않습니다",
                )

        hashed_password = get_password_hash(new_password)
        stmt = (
            update(SystemAdmin)
            .where(SystemAdmin.id == current_user.id)
            .values(password=hashed_password)
        )
        await db.execute_query(stmt, schemas=schemas)
    else:
        tenant_schema = payload.get("tenant_schema")
        if not tenant_schema:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다.",
            )

        schemas = [tenant_schema, "public"]
        stmt = select(models.User).where(models.User.id == user_id)
        row = await db.execute_query(stmt, schemas=schemas)
        current_user = row.scalar_one_or_none()
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자를 찾을 수 없습니다.",
            )

        if not is_temp_password:
            if not old_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="현재 비밀번호를 입력해주세요",
                )
            if not verify_password(old_password, current_user.password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="현재 비밀번호가 올바르지 않습니다",
                )

        hashed_password = get_password_hash(new_password)
        stmt = (
            update(models.User)
            .where(models.User.id == current_user.id)
            .values(password=hashed_password)
        )
        await db.execute_query(stmt, schemas=schemas)

    return {"message": "비밀번호가 변경되었습니다"}


def logout_service(*, token: str) -> Dict[str, str]:
    """
    단일 세션 로그아웃.
    """
    session_manager.delete_session(token)
    return {"message": "로그아웃되었습니다"}


def logout_all_service(*, user_id: int) -> Dict[str, str]:
    """
    모든 기기 로그아웃.
    """
    session_manager.delete_all_user_sessions(user_id)
    return {"message": "모든 기기에서 로그아웃되었습니다"}


def set_token_expire_service(*, user_id: int, expire_minutes: int) -> Dict[str, Any]:
    """
    사용자별 토큰 유효기간 설정.
    """
    session_manager.set_user_token_expire_minutes(
        user_id=user_id,
        expire_minutes=expire_minutes,
    )
    return {
        "message": f"토큰 유효기간이 {expire_minutes}분으로 설정되었습니다",
        "expire_minutes": expire_minutes,
    }


def get_token_expire_service(*, user_id: int) -> Dict[str, Any]:
    """
    사용자별 토큰 유효기간 조회.
    """
    expire_minutes = session_manager.get_user_token_expire_minutes(
        user_id=user_id,
        default=ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return {
        "expire_minutes": expire_minutes,
        "default": ACCESS_TOKEN_EXPIRE_MINUTES,
    }


