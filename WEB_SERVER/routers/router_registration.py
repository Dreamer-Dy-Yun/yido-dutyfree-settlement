###########################################
# Module name : router_registration.py
# Module functions : 회원가입 관련 엔드포인트
#                   회원가입, 이메일 인증
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.01.30
# Updated at : 2026.01.30
# Supported by : Cursor AI
# Note : 
############################################

import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from DATABASE.repositories import UserRepository, TenantRepository
from WEB_SERVER.routers.settings import get_user_repository, get_tenant_repository
from WEB_SERVER.auth import get_password_hash
from WEB_SERVER.services.service_email import email_service
from WEB_SERVER.services.verification_token import verification_token_service
from CUSTOMIZED.cust_deco_error import handle_http_error
import pandas as pd

router = APIRouter(prefix="/api/registration", tags=["회원가입"])


# 요청/응답 스키마
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str | None = None
    company_name: str  # 회사명 (테넌트)


# 회원가입
@router.post("/register", summary="회원가입", description="새로운 사용자를 등록합니다. 이메일 인증 후 활성화됩니다.")
@handle_http_error
async def register(
    user_data: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    # 이메일 중복 확인
    existing_email = await user_repo.get_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 이메일입니다"
        )
    
    # 테넌트(회사) 조회 또는 생성
    tenant = await tenant_repo.get_or_create(
        name=user_data.company_name,
        description=f"{user_data.company_name} 회사"
    )
    
    # 비밀번호 해싱
    hashed_password = get_password_hash(user_data.password)
    
    # 사용자 생성 (이메일 인증 전까지 비활성화)
    user_df = pd.DataFrame([{
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "full_name": user_data.full_name,
        "tenant_id": tenant.id,  # 테넌트 ID 추가
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
        created_user.id  # ORM 객체이므로 .id로 접근
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
        "email": user_data.email,
        "company_name": user_data.company_name
    }


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
