###########################################
# Module name : router_company.py
# Module functions : 회사 검색 및 등록 관련 엔드포인트
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.20
# Note : 회사 선택, 검색, 신규 등록
#       리팩토링 필요. 코드가 개판임
############################################

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, EmailStr
from DATABASE.repositories.authorities import TenantRepository
from WEB_SERVER.routers.settings import get_tenant_repository, get_db_manager
from DATABASE.dbms import DBManager
from CUSTOMIZED.cust_deco_error import handle_http_error
from WEB_SERVER.services.company_service import (
    search_company_service,
    register_company_service,
)

router = APIRouter(prefix="/api/company", tags=["회사"])


# 요청/응답 스키마
class CompanySearchRequest(BaseModel):
    name: str | None = None
    business_no: str | None = None


class CompanyInfo(BaseModel):
    id: int
    name: str
    alias: str | None
    business_no: str | None
    is_active: bool

    class Config:
        from_attributes = True


class CompanyRegisterRequest(BaseModel):
    name: str  # 회사명
    alias: str | None = None  # 회사 별칭
    business_no: str | None = None  # 사업자 번호
    country_code: int | None = None  # 국가 코드
    contact: str | None = None  # 대표번호
    email: EmailStr | None = None  # 대표 이메일
    address: str | None = None  # 소재지
    use_existing_if_pending: bool = False  # 이미 등록된 사업자번호가 있고 DB가 생성되지 않은 경우 기존 테넌트로 계속 진행할지 여부


# 회사 검색
@router.get("/search", summary="회사 검색", description="회사명 또는 사업자번호로 회사를 검색합니다.")
@handle_http_error
async def search_company(
    name: str | None = Query(None, description="회사명"),
    business_no: str | None = Query(None, description="사업자번호"),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """회사 검색"""
    return await search_company_service(
        name=name,
        business_no=business_no,
        tenant_repo=tenant_repo,
    )


# 신규 회사 등록
@router.post("/register", summary="신규 회사 등록", description="새로운 회사를 등록합니다. 관리자 승인 후 활성화됩니다.")
@handle_http_error
async def register_company(
    company_data: CompanyRegisterRequest,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: DBManager = Depends(get_db_manager),
):
    """신규 회사 등록"""
    return await register_company_service(
        name=company_data.name,
        alias=company_data.alias,
        business_no=company_data.business_no,
        country_code=company_data.country_code,
        contact=company_data.contact,
        email=str(company_data.email) if company_data.email is not None else None,
        address=company_data.address,
        use_existing_if_pending=company_data.use_existing_if_pending,
        tenant_repo=tenant_repo,
        db=db,
    )
