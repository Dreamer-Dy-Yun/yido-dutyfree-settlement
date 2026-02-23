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
from fastapi import Depends, HTTPException, status
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
    db: DBManager = Depends(get_db_manager)
) -> models.User:
    """현재 로그인한 사용자 조회 (Redis 세션 검증 포함, 테넌트 스키마에서 조회)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
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
                detail="세션이 만료되었거나 로그아웃되었습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    except (JWTError, ValueError):
        raise credentials_exception
    
    # 테넌트 스키마로 전환
    await db.set_schemas([tenant_schema, "public"])
    
    # 테넌트 스키마에서 사용자 조회
    stmt = select(models.User).where(models.User.id == user_id)
    result = await db.execute_query(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다"
        )
    
    # 세션 연장 (활동 시 자동 연장)
    # 사용자별 토큰 유효기간 사용
    user_token_expire_minutes = session_manager.get_user_token_expire_minutes(
        user_id=user.id,
        default=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    expires_in = user_token_expire_minutes * 60  # 분을 초로 변환
    session_manager.extend_session(token, expires_in)
    
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
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager)
) -> models.User:
    """서비스 제공사 관리자 권한 확인 (public 스키마의 ServiceEmail에서 확인)"""
    from DATABASE.models.public_model import ServiceEmail
    
    # public 스키마로 전환
    await db.set_schemas(["public"])
    
    # ServiceEmail에서 확인 (이메일로 조회)
    stmt = select(ServiceEmail).where(
        ServiceEmail.e_mail == current_user.e_mail,
        ServiceEmail.is_active == True
    )
    result = await db.execute_query(stmt)
    service_email = result.scalar_one_or_none()
    
    if not service_email or service_email.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="서비스 제공사 관리자 권한이 필요합니다"
        )
    
    return current_user


async def get_current_tenant_admin(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """테넌트 관리자 권한 확인 (tenant 스키마의 User)"""
    # tenant 스키마의 User 모델을 사용하므로 role 필드 확인
    if not hasattr(current_user, 'role') or current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="테넌트 관리자 권한이 필요합니다"
        )
    return current_user
