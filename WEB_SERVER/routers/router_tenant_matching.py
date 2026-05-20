###########################################
# Module name : router_tenant_matching.py
# Module functions : Tenant matching aggregator
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.05.20
# Note : Included by router_tenant.py; do not duplicate /api/tenant prefix here.
############################################

from fastapi import APIRouter

from WEB_SERVER.routers.router_tenant_match_jobs import router as match_jobs_router
from WEB_SERVER.routers.router_tenant_match_results import router as match_results_router
from WEB_SERVER.routers.router_tenant_verification import router as verification_router

router = APIRouter()
router.include_router(match_jobs_router)
router.include_router(match_results_router)
router.include_router(verification_router)
