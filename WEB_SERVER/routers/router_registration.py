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

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, EmailStr
from DATABASE.repositories import UserRepository, TenantRepository
from DATABASE.dbms import DBManager
from WEB_SERVER.routers.settings import (
    get_user_repository,
    get_tenant_repository,
    get_db_manager,
)
from CUSTOMIZED.cust_deco_error import handle_http_error
from WEB_SERVER.services.registration_service import (
    register_user_service,
    verify_email_service,
)

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
    db: DBManager = Depends(get_db_manager),
):
    return await register_user_service(
        username=user_data.username,
        email=str(user_data.email),
        password=user_data.password,
        full_name=user_data.full_name,
        company_name=user_data.company_name,
        user_repo=user_repo,
        tenant_repo=tenant_repo,
        db=db,
    )


# 이메일 인증
@router.get("/verify-email", summary="이메일 인증", description="이메일 인증 토큰을 검증하고 사용자를 활성화합니다.")
@handle_http_error
async def verify_email(
    token: str = Query(..., description="인증 토큰"),
    email: str = Query(..., description="이메일 주소"),
    user_repo: UserRepository = Depends(get_user_repository),
    db: DBManager = Depends(get_db_manager),
):
    """이메일 인증 처리"""
    return await verify_email_service(
        token=token,
        email=email,
        user_repo=user_repo,
        db=db,
    )
