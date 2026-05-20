###########################################
# Module name : router_system_admin_dashboard.py
# Module functions : 시스템 어드민 대시보드 통계 API
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.24
# Supported by : Cursor AI
# Note : router_system_admin aggregator 하위 대시보드 라우터
############################################

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select

from WEB_SERVER.auth.dependencies import get_current_superuser
from WEB_SERVER.routers.settings import get_db_manager, get_tenant_repository
from CUSTOMIZED.cust_deco_error import handle_http_error

from DATABASE import models
from DATABASE.models.public_model import ServiceAccount, ServiceAccountRole
from DATABASE.repositories.authorities import TenantRepository
from DATABASE.dbms import DBManager

router = APIRouter()


class SystemStatsResponse(BaseModel):
    total_tenants: int
    active_tenants: int
    pending_tenants: int
    total_service_accounts: int
    active_service_accounts: int
    has_smtp_account: bool


@router.get("/dashboard/stats", summary="시스템 통계 조회", description="전체 시스템 통계를 조회합니다.")
@handle_http_error
async def get_system_stats(
    current_user: models.User = Depends(get_current_superuser),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    db: DBManager = Depends(get_db_manager),
):
    """시스템 전체 통계 조회"""
    schemas = ["public"]

    all_tenants = await tenant_repo.get_all()
    active_tenants = await tenant_repo.get_all(is_active=True)
    pending_tenants = await tenant_repo.get_all(is_active=False)

    stmt_total = select(func.count(ServiceAccount.id))
    result_total = await db.execute_query(stmt_total, schemas=schemas)
    total_service_accounts = result_total.scalar() or 0

    stmt_active = select(func.count(ServiceAccount.id)).where(ServiceAccount.is_active == True)
    result_active = await db.execute_query(stmt_active, schemas=schemas)
    active_service_accounts = result_active.scalar() or 0

    stmt = select(ServiceAccount).where(
        ServiceAccount.role == ServiceAccountRole.SMTP_SENDER.value,
        ServiceAccount.is_active == True,
    ).limit(1)
    result = await db.execute_query(stmt, schemas=schemas)
    has_smtp_account = result.scalar_one_or_none() is not None

    return SystemStatsResponse(
        total_tenants=len(all_tenants),
        active_tenants=len(active_tenants),
        pending_tenants=len(pending_tenants),
        total_service_accounts=total_service_accounts,
        active_service_accounts=active_service_accounts,
        has_smtp_account=has_smtp_account,
    )
