###########################################
# Module name : router_system_admin_tenants.py
# Module functions : 시스템 어드민 테넌트 생명주기 API
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.24
# Supported by : Cursor AI
# Note : router_system_admin aggregator 하위 테넌트 라우터
############################################

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr

from WEB_SERVER.auth.dependencies import get_current_superuser
from WEB_SERVER.routers.router_system_admin_tenant_lifecycle import router as lifecycle_router
from WEB_SERVER.routers.settings import get_tenant_repository
from CUSTOMIZED.cust_deco_error import handle_http_error

from DATABASE import models
from DATABASE.repositories.authorities import TenantRepository

router = APIRouter()
router.include_router(lifecycle_router)


class TenantUpdateRequest(BaseModel):
    name: str | None = None
    alias: str | None = None
    country_code: str | None = None
    contact: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    is_active: bool | None = None


@router.get("/tenants", summary="테넌트 목록 조회", description="모든 테넌트 목록을 조회합니다.")
@handle_http_error
async def get_tenants(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 레코드 수"),
    is_active: bool | None = Query(None, description="활성화 여부 필터"),
    search: str | None = Query(None, description="검색어 (회사명, 사업자번호)"),
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """테넌트 목록 조회"""
    tenants = await tenant_repo.get_all(skip=skip, limit=limit, is_active=is_active)

    if search:
        search_lower = search.lower()
        tenants = [
            t for t in tenants
            if search_lower in t.get("name", "").lower()
            or search_lower in t.get("business_no", "").lower()
        ]

    return {
        "tenants": tenants,
        "total": len(tenants),
        "skip": skip,
        "limit": limit,
    }


@router.get("/tenants/pending", summary="승인 대기 테넌트 목록", description="승인 대기 중인 테넌트 목록을 조회합니다.")
@handle_http_error
async def get_pending_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """승인 대기 테넌트 목록 조회"""
    tenants = await tenant_repo.get_all(skip=skip, limit=limit, is_active=False)
    return {
        "pending_tenants": tenants,
        "total": len(tenants),
        "skip": skip,
        "limit": limit,
    }


@router.get("/tenants/{tenant_id}", summary="테넌트 상세 조회", description="특정 테넌트의 상세 정보를 조회합니다.")
@handle_http_error
async def get_tenant_detail(
    tenant_id: int,
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """테넌트 상세 조회"""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="테넌트를 찾을 수 없습니다"
        )

    tenant_dict = tenant.to_dict()
    tenant_dict["created_at"] = tenant_dict.pop("db_created_at").isoformat() if tenant_dict.get("db_created_at") else None
    tenant_dict["updated_at"] = tenant_dict.pop("db_updated_at").isoformat() if tenant_dict.get("db_updated_at") else None

    return tenant_dict


@router.put("/tenants/{tenant_id}", summary="테넌트 정보 수정", description="테넌트 정보를 수정합니다.")
@handle_http_error
async def update_tenant(
    tenant_id: int,
    update_data: TenantUpdateRequest,
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """테넌트 정보 수정"""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="테넌트를 찾을 수 없습니다"
        )

    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 데이터가 없습니다"
        )

    await tenant_repo.update(tenant_id, update_dict)

    updated_tenant = await tenant_repo.get_by_id(tenant_id)

    return {
        "message": "테넌트 정보가 수정되었습니다",
        "tenant": {
            "id": updated_tenant.id,
            "name": updated_tenant.name,
            "alias": updated_tenant.alias,
            "business_no": updated_tenant.business_no,
            "contact": updated_tenant.contact,
            "email": updated_tenant.email,
            "address": updated_tenant.address,
            "is_active": updated_tenant.is_active,
        },
        "updated_at": datetime.now().isoformat(),
        "updated_by": current_user.e_mail,
    }


@router.post("/tenants/{tenant_id}/activate", summary="테넌트 활성화", description="테넌트를 활성화합니다.")
@handle_http_error
async def activate_tenant(
    tenant_id: int,
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """테넌트 활성화"""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="테넌트를 찾을 수 없습니다"
        )

    if tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 활성화된 테넌트입니다"
        )

    await tenant_repo.update(tenant_id, {"is_active": True})

    return {
        "message": "테넌트가 활성화되었습니다",
        "tenant_id": tenant_id,
        "activated_at": datetime.now().isoformat(),
        "activated_by": current_user.e_mail,
    }


@router.post("/tenants/{tenant_id}/deactivate", summary="테넌트 비활성화", description="테넌트를 비활성화합니다. (스키마 및 데이터는 유지)")
@handle_http_error
async def deactivate_tenant(
    tenant_id: int,
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """테넌트 비활성화 (스키마 및 데이터 유지)"""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="테넌트를 찾을 수 없습니다"
        )

    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 비활성화된 테넌트입니다"
        )

    await tenant_repo.update(tenant_id, {"is_active": False})

    return {
        "message": "테넌트가 비활성화되었습니다",
        "tenant_id": tenant_id,
        "deactivated_at": datetime.now().isoformat(),
        "deactivated_by": current_user.e_mail,
    }

