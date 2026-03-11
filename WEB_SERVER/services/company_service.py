###########################################
# Module name : company_service.py
# Module functions : 회사 검색/등록 비즈니스 로직
# Written by : Cursor AI (with Yun Dae-young)
############################################

from typing import Any, Dict, List
import uuid

from fastapi import HTTPException, status
import pandas as pd
from sqlalchemy import select, or_

from DATABASE import models
from DATABASE.dbms import DBManager
from DATABASE.repositories.authorities import TenantRepository
from WEB_SERVER.services.service_email import email_service, get_db_smtp_email_service


async def search_company_service(
    *,
    name: str | None,
    business_no: str | None,
    tenant_repo: TenantRepository,
) -> List[Dict[str, Any]]:
    """
    회사 검색 비즈니스 로직.
    """
    stmt = select(models.Tenant)
    conditions = []

    if name:
        conditions.append(
            or_(
                models.Tenant.name.ilike(f"%{name}%"),
                models.Tenant.alias.ilike(f"%{name}%"),
            )
        )
    if business_no:
        conditions.append(models.Tenant.business_no == business_no)

    if not conditions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="회사명 또는 사업자번호를 입력해주세요",
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


async def register_company_service(
    *,
    name: str,
    alias: str | None,
    business_no: str | None,
    country_code: int | None,
    contact: str | None,
    email: str | None,
    address: str | None,
    use_existing_if_pending: bool,
    tenant_repo: TenantRepository,
    db: DBManager,
) -> Dict[str, Any]:
    """
    신규 회사 등록 비즈니스 로직.
    """
    existing_tenant = None

    if business_no:
        result = await tenant_repo.db.execute_query(
            select(models.Tenant).where(models.Tenant.business_no == business_no)
        )
        existing_tenant = result.scalar_one_or_none()

        if existing_tenant:
            if getattr(existing_tenant, "is_db_built", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 사업자번호입니다",
                )
            if not use_existing_if_pending:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 사업자번호입니다. 계속 진행할까요?",
                )

    if (
        existing_tenant
        and not getattr(existing_tenant, "is_db_built", False)
        and use_existing_if_pending
    ):
        update_data = {
            "name": name,
            "alias": alias,
            "business_no": business_no,
            "country_code": country_code,
            "contact": contact,
            "email": email,
            "address": address,
        }
        await tenant_repo.update(existing_tenant.id, update_data)
        tenant = await tenant_repo.get_by_id(existing_tenant.id)
    else:
        uuid_str = str(uuid.uuid4()).replace("-", "")
        schema_name = f"company_{uuid_str}"
        dir_base = f"tenants/{schema_name}"

        tenant_df = pd.DataFrame(
            [
                {
                    "name": name,
                    "alias": alias,
                    "business_no": business_no,
                    "country_code": country_code,
                    "contact": contact,
                    "email": email,
                    "address": address,
                    "dir_base": dir_base,
                    "schema_name": schema_name,
                    "is_active": False,
                }
            ]
        )

        await tenant_repo.create(tenant_df)

        if business_no:
            result = await tenant_repo.db.execute_query(
                select(models.Tenant).where(models.Tenant.business_no == business_no)
            )
            tenant = result.scalar_one_or_none()
        else:
            tenant = await tenant_repo.get_by_name(name)

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="회사 등록에 실패했습니다",
            )

    if email:
        smtp_service = await get_db_smtp_email_service(db) or email_service
        smtp_service.set_company_registration_email(
            receiver_email=email,
            company_name=name,
            business_no=business_no,
            contact=contact,
        ).send(
            log_success=f"회사 등록 안내 이메일 발송 완료: {email}",
            log_error=f"회사 등록 안내 이메일 발송 실패: {email}",
        )

    return {
        "message": "회사 등록이 완료되었습니다. 관리자 승인 후 활성화됩니다.",
        "company_id": tenant.id,
        "company_name": tenant.name,
        "schema_name": tenant.schema_name,
    }


