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
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import timedelta
from DATABASE.repositories import UserRepository
from WEB_SERVER.routers.settings import get_user_repository
from WEB_SERVER.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    oauth2_scheme
)
from WEB_SERVER.auth.redis_session import session_manager
from WEB_SERVER.auth.google_oauth import (
    get_google_authorization_url,
    generate_state_token,
    get_google_user_info
)
from WEB_SERVER.services.service_email import email_service
from WEB_SERVER.services.verification_token import verification_token_service
from DATABASE import models
from CUSTOMIZED.cust_deco_error import handle_http_error
import pandas as pd
import secrets

router = APIRouter(prefix="/api/auth", tags=["인증"])


# 요청/응답 스키마
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str | None
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


# 회원가입
@router.post("/register", summary="회원가입", description="새로운 사용자를 등록합니다.")
@handle_http_error
async def register(
    user_data: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository),
):
    # 이메일 중복 확인
    existing_email = await user_repo.get_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 이메일입니다"
        )
    
    # 비밀번호 해싱
    hashed_password = get_password_hash(user_data.password)
    
    # 사용자 생성 (이메일 인증 전까지 비활성화)
    user_df = pd.DataFrame([{
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "full_name": user_data.full_name,
        "is_active": False,  # 이메일 인증 전까지 비활성화
        "is_superuser": False
    }])
    
    await user_repo.create(user_df)
    
    # 생성된 사용자 조회 (ID 필요)
    created_user = await user_repo.get_by_email(user_data.email)
    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 생성 후 조회에 실패했습니다"
        )
    
    # 인증 토큰 생성 및 저장
    verification_token = verification_token_service.generate_token(user_data.email)
    verification_token_service.save_token(
        user_data.email,
        verification_token,
        created_user.id
    )
    
    # 인증 이메일 발송
    app_url = os.getenv("APP_URL", "http://localhost:3001")
    email_service.set_verification_email(
        receiver_email=user_data.email,
        receiver_name=user_data.username,
        verification_token=verification_token,
        service_url=app_url
    ).send(log=f"인증 이메일 발송 완료: {user_data.email}")
    
    return {
        "message": "회원가입이 완료되었습니다. 이메일을 확인하여 인증을 완료해주세요.",
        "username": user_data.username,
        "email": user_data.email
    }


# 로그인
@router.post("/login", summary="로그인", description="사용자 인증 후 JWT 토큰을 발급합니다.", response_model=Token)
@handle_http_error
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repository),
):
    # 이메일로 사용자 조회
    user = await user_repo.get_by_email(form_data.username)  # OAuth2PasswordRequestForm의 username 필드에 이메일 입력
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 비밀번호 확인
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 활성화 여부 확인 (이메일 인증 완료 여부)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이메일 인증이 완료되지 않았습니다. 이메일을 확인하여 인증을 완료해주세요."
        )
    
    # 마지막 로그인 시간 업데이트
    await user_repo.update_last_login(user.id)
    
    # 사용자별 토큰 유효기간 조회 (기본값은 전역 설정)
    user_token_expire_minutes = session_manager.get_user_token_expire_minutes(
        user_id=user.id,
        default=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    # 액세스 토큰 생성 (이메일을 sub에 저장)
    access_token_expires = timedelta(minutes=user_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Redis에 세션 저장
    expires_in_seconds = user_token_expire_minutes * 60
    session_manager.create_session(
        token=access_token,
        user_id=user.id,
        email=user.email,
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
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser
    }


# 토큰 갱신
@router.post("/refresh", summary="토큰 갱신", description="액세스 토큰을 갱신합니다.", response_model=Token)
@handle_http_error
async def refresh_token(
    current_user: models.User = Depends(get_current_active_user),
    old_token: str = Depends(oauth2_scheme),
):
    # 기존 토큰 삭제
    session_manager.delete_session(old_token)
    
    # 사용자별 토큰 유효기간 조회
    user_token_expire_minutes = session_manager.get_user_token_expire_minutes(
        user_id=current_user.id,
        default=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    # 새 토큰 생성
    access_token_expires = timedelta(minutes=user_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": current_user.email}, expires_delta=access_token_expires
    )
    
    # 새 토큰을 Redis에 저장
    expires_in_seconds = user_token_expire_minutes * 60
    session_manager.create_session(
        token=access_token,
        user_id=current_user.id,
        email=current_user.email,
        expires_in=expires_in_seconds
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# 사용자 비밀번호 변경
@router.post("/change-password", summary="비밀번호 변경", description="현재 사용자의 비밀번호를 변경합니다.")
@handle_http_error
async def change_password(
    old_password: str = Body(...),
    new_password: str = Body(...),
    current_user: models.User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    # 현재 비밀번호 확인
    user = await user_repo.get_by_id(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 올바르지 않습니다"
        )
    
    # 새 비밀번호 해싱 및 업데이트
    hashed_password = get_password_hash(new_password)
    await user_repo.update(current_user.id, {"hashed_password": hashed_password})
    
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


# Google OAuth 로그인 시작
@router.get("/google/login", summary="Google 로그인", description="Google OAuth 인증을 시작합니다.")
@handle_http_error
async def google_login(request: Request):
    """Google OAuth 로그인 시작 - Google 인증 페이지로 리다이렉트"""
    # CSRF 방지를 위한 state 토큰 생성
    state = generate_state_token()
    
    # 세션에 state 저장 (검증용)
    if not hasattr(request.app.state, "sessions"):
        request.app.state.sessions = {}
    request.app.state.sessions[state] = {
        "type": "google_oauth",
        "timestamp": pd.Timestamp.now()
    }
    
    # Google 인증 URL 생성
    authorization_url = get_google_authorization_url(state)
    
    return RedirectResponse(url=authorization_url)


# Google OAuth 콜백
@router.get("/google/callback", summary="Google 로그인 콜백", description="Google OAuth 인증 후 콜백을 처리합니다.", response_model=Token)
@handle_http_error
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    request: Request = None,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Google OAuth 콜백 처리"""
    # State 검증 (CSRF 방지)
    if not hasattr(request.app.state, "sessions") or state not in request.app.state.sessions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 state 토큰입니다"
        )
    
    # 세션에서 state 제거
    del request.app.state.sessions[state]
    
    # Google에서 사용자 정보 가져오기
    google_user_info = await get_google_user_info(code, state)
    
    if not google_user_info.get("email") or not google_user_info.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google 이메일 인증이 완료되지 않았습니다"
        )
    
    email = google_user_info["email"]
    name = google_user_info.get("name", "")
    
    # 기존 사용자 확인
    user = await user_repo.get_by_email(email)
    
    if not user:
        # 신규 사용자 자동 회원가입
        # username은 이메일의 @ 앞부분 사용
        username = email.split("@")[0]
        
        # 중복 방지를 위해 username이 이미 존재하면 이메일 전체를 username으로 사용
        existing_user = await user_repo.get_by_username(username)
        if existing_user:
            username = email
        
        # Google OAuth 사용자는 비밀번호가 없으므로 빈 해시값 저장 (또는 특별한 값)
        # 실제로는 Google OAuth 사용자는 비밀번호 없이 로그인하므로 hashed_password를 NULL로 할 수 있지만
        # 현재 모델이 nullable=False이므로 더미 값을 저장
        hashed_password = get_password_hash(secrets.token_urlsafe(32))  # 랜덤 비밀번호 생성
        
        user_df = pd.DataFrame([{
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "full_name": name,
            "is_active": True,
            "is_superuser": False
        }])
        
        await user_repo.create(user_df)
        
        # 생성된 사용자 다시 조회
        user = await user_repo.get_by_email(email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 생성 또는 조회에 실패했습니다"
        )
    
    # 활성화 여부 확인 (이메일 인증 완료 여부)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이메일 인증이 완료되지 않았습니다. 이메일을 확인하여 인증을 완료해주세요."
        )
    
    # 마지막 로그인 시간 업데이트
    await user_repo.update_last_login(user.id)
    
    # 사용자별 토큰 유효기간 조회 (기본값은 전역 설정)
    user_token_expire_minutes = session_manager.get_user_token_expire_minutes(
        user_id=user.id,
        default=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    # JWT 토큰 생성 (기존 로그인과 동일한 방식)
    access_token_expires = timedelta(minutes=user_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Redis에 세션 저장
    expires_in_seconds = user_token_expire_minutes * 60
    session_manager.create_session(
        token=access_token,
        user_id=user.id,
        email=user.email,
        expires_in=expires_in_seconds
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# 이메일 인증
@router.get("/verify-email", summary="이메일 인증", description="이메일 인증 토큰을 검증하고 사용자를 활성화합니다.")
@handle_http_error
async def verify_email(
    token: str = Query(..., description="인증 토큰"),
    email: str = Query(..., description="이메일 주소"),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """이메일 인증 처리"""
    # 토큰 검증
    token_data = verification_token_service.verify_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 토큰이거나 만료된 토큰입니다"
        )
    
    # 이메일 일치 확인
    if token_data['email'] != email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="토큰과 이메일이 일치하지 않습니다"
        )
    
    # 사용자 조회
    user = await user_repo.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 이미 활성화된 경우
    if user.is_active:
        # 토큰 삭제
        verification_token_service.delete_token(token)
        return {
            "message": "이미 인증이 완료된 계정입니다",
            "verified": True
        }
    
    # 사용자 활성화 (이메일 인증 완료)
    await user_repo.update(user.id, {"is_active": True})
    
    # 토큰 삭제
    verification_token_service.delete_token(token)
    
    # 환영 이메일 발송
    email_service.set_welcome_email(
        receiver_email=email,
        receiver_name=user.username
    ).send(log=f"환영 이메일 발송 완료: {email}")
    
    return {
        "message": "이메일 인증이 완료되었습니다",
        "verified": True,
        "email": email
    }

