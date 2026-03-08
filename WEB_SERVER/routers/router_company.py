###########################################
# Module name : router_company.py
# Module functions : 회사 검색 및 등록 관련 엔드포인트
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.20
# Note : 회사 선택, 검색, 신규 등록
#       리팩토링 필요. 코드가 개판임
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
from WEB_SERVER.services.service_email import email_service, get_db_smtp_email_service
import pandas as pd
import uuid

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
    stmt = select(models.Tenant)
    
    conditions = []
    if name:
        # 회사명 또는 별칭으로 검색
        conditions.append(
            or_(
                models.Tenant.name.ilike(f"%{name}%"),
                models.Tenant.alias.ilike(f"%{name}%")
            )
        )
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
    existing_tenant = None

    # 1) 사업자번호 중복/기존 테넌트 확인
    if company_data.business_no:
        result = await tenant_repo.db.execute_query(
            select(models.Tenant).where(models.Tenant.business_no == company_data.business_no)
        )
        existing_tenant = result.scalar_one_or_none()

        if existing_tenant:
            # 이미 DB가 생성된 테넌트라면 무조건 막는다.
            if getattr(existing_tenant, "is_db_built", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 사업자번호입니다"
                )
            # DB가 아직 생성되지 않은(승인 전) 테넌트인 경우
            if not company_data.use_existing_if_pending:
                # 프론트에서 팝업으로 한 번 더 확인받기 위한 에러
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 사업자번호입니다. 계속 진행할까요?"
                )

    # 2) 신규 생성 또는 기존 미구축 테넌트 재사용
    if existing_tenant and not getattr(existing_tenant, "is_db_built", False) and company_data.use_existing_if_pending:
        # 기존 테넌트 정보 업데이트 (필요한 필드만)
        update_data = {
            "name": company_data.name,
            "alias": company_data.alias,
            "business_no": company_data.business_no,
            "country_code": company_data.country_code,
            "contact": company_data.contact,
            "email": company_data.email,
            "address": company_data.address,
        }
        await tenant_repo.update(existing_tenant.id, update_data)
        tenant = await tenant_repo.get_by_id(existing_tenant.id)
    else:
        # ------------------------------------------------------------------
        # 새 테넌트 생성 플로우
        # 스키마명을 company_{UUID} 형태로 생성 (충돌 확률 거의 없음, 문자로 시작해서 안전)
        # ------------------------------------------------------------------

        # 스키마명/경로 생성 (UUID 사용 - 하이픈 제거)
        uuid_str = str(uuid.uuid4()).replace("-", "")  # 예: 550e8400e29b41d4a716446655440000 (32자)
        schema_name = f"company_{uuid_str}"  # 예: company_550e8400e29b41d4a716446655440000
        dir_base = f"tenants/{schema_name}"

        # 테넌트 생성 (is_active=False로 생성, 승인 대기 상태)
        tenant_df = pd.DataFrame([{
            "name": company_data.name,
            "alias": company_data.alias,
            "business_no": company_data.business_no,
            "country_code": company_data.country_code,
            "contact": company_data.contact,
            "email": company_data.email,  # 회사 대표 이메일 저장
            "address": company_data.address,
            "dir_base": dir_base,
            "schema_name": schema_name,
            "is_active": False,  # 승인 대기 상태
        }])

        await tenant_repo.create(tenant_df)

        # 생성된 테넌트 조회
        if company_data.business_no:
            # 사업자번호는 유니크이므로 우선적으로 사용
            result = await tenant_repo.db.execute_query(
                select(models.Tenant).where(models.Tenant.business_no == company_data.business_no)
            )
            tenant = result.scalar_one_or_none()
        else:
            # 사업자번호가 없으면 회사명 기준으로 조회
            tenant = await tenant_repo.get_by_name(company_data.name)

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="회사 등록에 실패했습니다"
            )

    # 대표 이메일로 회사 등록 안내 메일 발송
    if company_data.email:
        smtp_service = await get_db_smtp_email_service(db) or email_service
        smtp_service.set_company_registration_email(
            receiver_email=company_data.email,
            company_name=company_data.name,
            business_no=company_data.business_no,
            contact=company_data.contact,
        ).send(
            log_success=f"회사 등록 안내 이메일 발송 완료: {company_data.email}",
            log_error=f"회사 등록 안내 이메일 발송 실패: {company_data.email}",
        )

    return {
        "message": "회사 등록이 완료되었습니다. 관리자 승인 후 활성화됩니다.",
        "company_id": tenant.id,
        "company_name": tenant.name,
        "schema_name": tenant.schema_name,
    }
