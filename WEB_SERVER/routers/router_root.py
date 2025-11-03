from fastapi import APIRouter, Query, Response, HTTPException, Depends
from fastapi.responses import Response
from DATABASE.cruder import CRUDer
from pathlib import Path
import orjson
import gzip
import CUSTOMIZED.cust_parser as cp
from WEB_SERVER.routers.settings import get_cruder
from WEB_SERVER.routers.settings import get_db_manager
from WEB_SERVER.routers.settings import ffa
from sqlalchemy import text

router = APIRouter(prefix="", tags=["root"])

# 루트 엔드포인트
@router.get("/")
async def root():
    return {"message": "NOVAS EZ FastAPI 서버에 오신 걸 환영합니다!"}


@router.get("/health")
async def health_check():
    """기본 헬스체크 - 서버가 살아있는지 확인"""
    return {"status": "healthy", "service": "NOVAS EZ API"}


@router.get("/health/ready")
async def readiness_check(db_manager=Depends(get_db_manager)):
    """레디니스 체크 - DB 연결 등 서비스 준비 상태 확인"""
    try:
        # DB 연결 테스트
        await db_manager.execute_query(text("SELECT 1"))
        return {
            "status": "ready",
            "service": "NOVAS EZ API",
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

