###########################################
# Module name : router_system_admin.py
# Module functions : 시스템 어드민 전용 API (서비스 제공사 관리자)
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.24
# Supported by : Cursor AI
# Note : 시스템 어드민 전용 엔드포인트 aggregator
############################################

from fastapi import APIRouter

from WEB_SERVER.routers.router_system_admin_dashboard import router as dashboard_router
from WEB_SERVER.routers.router_system_admin_llm_api_keys import router as llm_api_keys_router
from WEB_SERVER.routers.router_system_admin_prompts import router as prompts_router
from WEB_SERVER.routers.router_system_admin_service_accounts import router as service_accounts_router
from WEB_SERVER.routers.router_system_admin_tenants import router as tenants_router

router = APIRouter(prefix="/api/system-admin", tags=["시스템 어드민"])
router.include_router(dashboard_router)
router.include_router(tenants_router)
router.include_router(service_accounts_router)
router.include_router(llm_api_keys_router)
router.include_router(prompts_router)
