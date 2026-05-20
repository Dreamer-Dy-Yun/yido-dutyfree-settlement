###########################################
# Module name : router_tenant.py
# Module functions : Tenant API aggregator
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.20
# Note : Keep /api/tenant prefix here and include sub-routers without duplicating it.
############################################

from fastapi import APIRouter

from WEB_SERVER.routers.router_tenant_edi import router as tenant_edi_router
from WEB_SERVER.routers.router_tenant_image import router as tenant_image_router
from WEB_SERVER.routers.router_tenant_matching import router as tenant_matching_router
from WEB_SERVER.routers.router_tenant_users import router as tenant_users_router

router = APIRouter(prefix="/api/tenant", tags=["테넌트 관리"])
router.include_router(tenant_users_router)
router.include_router(tenant_edi_router)
router.include_router(tenant_image_router)
router.include_router(tenant_matching_router)
