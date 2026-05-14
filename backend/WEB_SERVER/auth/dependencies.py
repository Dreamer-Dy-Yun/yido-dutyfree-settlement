###########################################
# Module name : dependencies.py
# Module functions : FastAPI 의존성 함수들
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Supported by : Chat GPT-4o / Cursor AI
# Note : get_current_user, get_current_active_user 등
############################################

from jose import JWTError
from fastapi import Depends, HTTPException, status, Response
from WEB_SERVER.auth.config import oauth2_scheme, ACCESS_TOKEN_EXPIRE_MINUTES
from WEB_SERVER.auth.jwt import decode_token
from WEB_SERVER.auth.redis_session import session_manager
from WEB_SERVER.routers.settings import get_db_manager
from DATABASE import models
from DATABASE.dbms import DBManager
from DATABASE.models.tenant_model import UserRole
from sqlalchemy import select


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: DBManager = Depends(get_db_manager),
    response: Response = None,
) -> models.User:
    """현재 로그인한 사용자 조회 (Redis 세션 검증 포함, 테넌트 스키마에서 조회)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="토큰이 만료되었거나 유효하지 않습니다. 다시 로그인 해 주세요",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # JWT 토큰 디코딩
        payload = decode_token(token)
        email: str = payload.get("sub")
        tenant_schema: str = payload.get("tenant_schema")
        user_id: int = payload.get("user_id")
        
        if email is None or tenant_schema is None or user_id is None:
            raise credentials_exception
        
        # Redis에서 세션 확인 (세션이 없으면 로그아웃된 토큰)
        if not session_manager.is_session_valid(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰이 만료되었습니다. 다시 로그인 해 주세요",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    except (JWTError, ValueError):
        raise credentials_exception
    
    schemas = [tenant_schema, "public"]

    # 테넌트 스키마에서 사용자 조회
    stmt = select(models.User).where(models.User.id == user_id)
    result = await db.execute_query(stmt, schemas=schemas)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다"
        )

    # 후속 라우터에서 tenant_schema를 명시적으로 전달할 수 있도록 주입
    setattr(user, "tenant_schema", tenant_schema)

    # 세션 연장 (활동 시 자동 연장)
    # 사용자별 토큰 유효기간 사용
    user_token_expire_minutes = session_manager.get_user_token_expire_minutes(
        user_id=user.id,
        default=ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    expires_in = user_token_expire_minutes * 60  # 분을 초로 변환
    session_manager.extend_session(token, expires_in)
    
    # 현재 세션 남은 시간(초)을 헤더에 노출
    if response is not None:
        ttl_seconds = session_manager.get_session_ttl(token)
        if ttl_seconds is not None:
            # 예: X-Session-Expires-In: 1740
            response.headers["X-Session-Expires-In"] = str(ttl_seconds)
    
    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """활성화된 현재 사용자 조회"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다"
        )
    return current_user


async def get_current_superuser(
    token: str = Depends(oauth2_scheme),
    db: DBManager = Depends(get_db_manager),
    response: Response = None,
):
    """서비스 제공사 관리자 권한 확인 (public 스키마의 SystemAdmin에서 확인, 세션 매니저 적용)"""
    from DATABASE.models.public_model import SystemAdmin
    
    # JWT 토큰에서 이메일 및 권한 정보 추출
    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        is_superuser: bool = payload.get("is_superuser", False)
        user_id: int | None = payload.get("user_id")
        
        if not email or not is_superuser or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="서비스 제공사 관리자 권한이 필요합니다",
            )
        
        # Redis 세션 확인 (세션이 없으면 만료/로그아웃된 토큰)
        if not session_manager.is_session_valid(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰이 만료되었습니다. 다시 로그인 해 주세요",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었거나 유효하지 않습니다. 다시 로그인 해 주세요",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # SystemAdmin에서 확인 (이메일로 조회)
    schemas = ["public"]
    stmt = select(SystemAdmin).where(
        SystemAdmin.e_mail == email,
        SystemAdmin.is_active == True,
    )
    result = await db.execute_query(stmt, schemas=schemas)
    system_admin = result.scalar_one_or_none()
    
    if not system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="서비스 제공사 관리자 권한이 필요합니다",
        )
    
    # 세션 연장 (활동 시 자동 연장) — 시스템 관리자도 동일 정책 적용
    admin_token_expire_minutes = session_manager.get_user_token_expire_minutes(
        user_id=user_id,
        default=ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    admin_expires_in = admin_token_expire_minutes * 60
    session_manager.extend_session(token, admin_expires_in)
    
    # 현재 세션 남은 시간(초)을 헤더에 노출
    if response is not None:
        ttl_seconds = session_manager.get_session_ttl(token)
        if ttl_seconds is not None:
            response.headers["X-Session-Expires-In"] = str(ttl_seconds)
    
    return system_admin


async def get_current_tenant_admin(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """테넌트 관리자 권한 확인 (tenant 스키마의 User)"""
    # tenant 스키마의 User 모델을 사용하므로 role 필드 확인
    # role은 문자열로 저장되므로 UserRole.ADMIN.value와 비교
    if not hasattr(current_user, 'role') or current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="테넌트 관리자 권한이 필요합니다"
        )
    return current_user
