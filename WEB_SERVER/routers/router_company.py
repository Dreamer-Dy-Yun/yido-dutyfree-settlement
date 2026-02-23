###########################################
# Module name : router_company.py
# Module functions : 회사 검색 및 등록 관련 엔드포인트
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.20
# Note : 회사 선택, 검색, 신규 등록
############################################

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from typing import Any
from sqlalchemy import select, or_
from DATABASE import models
from DATABASE.repositories.authorities import TenantRepository
from WEB_SERVER.routers.settings import get_tenant_repository, get_db_manager
from DATABASE.dbms import DBManager
from CUSTOMIZED.cust_deco_error import handle_http_error
import pandas as pd
import secrets
import string

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
    admin_email: EmailStr  # 관리자 이메일 (필수)
    admin_name: str  # 관리자 이름 (필수)


# 회사 검색
@router.get("/search", summary="회사 검색", description="회사명 또는 사업자번호로 회사를 검색합니다.")
@handle_http_error
async def search_company(
    name: str | None = Query(None, description="회사명"),
    business_no: str | None = Query(None, description="사업자번호"),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """회사 검색"""
    stmt = select(models.Tenant)
    
    conditions = []
    if name:
        conditions.append(models.Tenant.name.ilike(f"%{name}%"))
    if business_no:
        conditions.append(models.Tenant.business_no == business_no)
    
    if not conditions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="회사명 또는 사업자번호를 입력해주세요"
        )
    
    stmt = stmt.where(or_(*conditions))
    result = await tenant_repo.db.execute_query(stmt)
    tenants = result.scalars().all()
    
    return [
        {
            "id": tenant.id,
            "name": tenant.name,
            "alias": tenant.alias,
            "business_no": tenant.business_no,
            "is_active": tenant.is_active,
        }
        for tenant in tenants
    ]


# 신규 회사 등록
@router.post("/register", summary="신규 회사 등록", description="새로운 회사를 등록합니다. 관리자 승인 후 활성화됩니다.")
@handle_http_error
async def register_company(
    company_data: CompanyRegisterRequest,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: DBManager = Depends(get_db_manager),
):
    """신규 회사 등록"""
    # 사업자번호 중복 확인
    if company_data.business_no:
        existing = await tenant_repo.db.execute_query(
            select(models.Tenant).where(models.Tenant.business_no == company_data.business_no)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 사업자번호입니다"
            )
    
    # 스키마 이름 생성 (회사명 기반, 중복 방지)
    base_schema_name = company_data.name.lower().replace(" ", "_").replace("-", "_")
    schema_name = base_schema_name
    counter = 1
    
    while True:
        existing = await tenant_repo.db.execute_query(
            select(models.Tenant).where(models.Tenant.schema_name == schema_name)
        )
        if not existing.scalar_one_or_none():
            break
        schema_name = f"{base_schema_name}_{counter}"
        counter += 1
    
    # path_root 생성 (스키마 이름 기반)
    path_root = f"tenants/{schema_name}"
    
    # 테넌트 생성 (is_active=False로 생성, 승인 대기 상태)
    # 관리자 이메일은 email 필드에 저장
    tenant_df = pd.DataFrame([{
        "name": company_data.name,
        "alias": company_data.alias,
        "business_no": company_data.business_no,
        "country_code": company_data.country_code,
        "contact": company_data.contact,
        "email": company_data.admin_email,  # 관리자 이메일 저장
        "address": company_data.address,
        "path_root": path_root,
        "schema_name": schema_name,
        "is_active": False,  # 승인 대기 상태
    }])
    
    await tenant_repo.create(tenant_df)
    
    # 생성된 테넌트 조회
    tenant = await tenant_repo.get_by_name(company_data.name)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회사 등록에 실패했습니다"
        )
    
    return {
        "message": "회사 등록이 완료되었습니다. 관리자 승인 후 활성화됩니다.",
        "company_id": tenant.id,
        "company_name": tenant.name,
        "schema_name": tenant.schema_name,
    }
