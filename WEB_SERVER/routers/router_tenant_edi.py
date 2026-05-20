###########################################
# Module name : router_tenant_edi.py
# Module functions : Tenant EDI API aggregator
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.05.20
# Note : Included by router_tenant.py; do not duplicate the /api/tenant prefix here.
############################################

from fastapi import APIRouter

from WEB_SERVER.routers.router_tenant_edi_exports import router as edi_exports_router
from WEB_SERVER.routers.router_tenant_edi_jobs import router as edi_jobs_router

router = APIRouter()
router.include_router(edi_jobs_router)
router.include_router(edi_exports_router)
