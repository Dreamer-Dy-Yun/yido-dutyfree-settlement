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
from WEB_SERVER.routers.settings import get_user_repository
from DATABASE import models
from DATABASE.repositories.authorities import UserRepository


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repository: UserRepository = Depends(get_user_repository)
) -> models.User:
    """현재 로그인한 사용자 조회 (Redis 세션 검증 포함)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # JWT 토큰 디코딩
        payload = decode_token(token)
        email: str = payload.get("sub")
        if email is None:
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
    
    # Repository를 통해 사용자 조회 (ORM 객체 반환)
    user = await user_repository.get_by_email(email)
    
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
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """슈퍼유저 권한 확인"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 부족합니다"
        )
    return current_user


def check_permission(user: models.User, resource: str, action: str) -> bool:
    """사용자가 특정 리소스에 대한 특정 액션 권한을 가지고 있는지 확인"""
    # 슈퍼유저는 모든 권한 보유
    if user.is_superuser:
        return True
    
    # 사용자의 모든 역할에서 권한 확인
    for role in user.roles:
        if not role.is_active:
            continue
        for permission in role.permissions:
            if permission.resource == resource and permission.action == action:
                return True
    
    return False


async def require_permission(resource: str, action: str):
    """권한 체크 의존성 함수"""
    async def permission_checker(current_user: models.User = Depends(get_current_user)) -> models.User:
        if not check_permission(current_user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{resource}에 대한 {action} 권한이 없습니다"
            )
        return current_user
    
    return permission_checker
