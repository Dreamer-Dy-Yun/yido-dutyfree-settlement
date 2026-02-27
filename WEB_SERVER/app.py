import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from WEB_SERVER.routers.router_auth import router as router_auth
from fastapi.middleware.cors import CORSMiddleware
from DATABASE.config import db_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 DB 테이블 및 인덱스 초기화"""
    # Startup
    # public 스키마 테이블 생성
    await db_manager.create_tables(schema="public")
    yield
    # Shutdown (필요시 추가)


app = FastAPI(
    title="NOVAS EZ API",
    description="NOVAS EZ 프로젝트 FastAPI 예제",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 미들웨어 설정
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3001,http://192.168.0.19:5173,http://192.168.0.19:3001,http://172.23.112.1:5173,http://172.23.112.1:3001").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_origin_regex=r"http://(192\.168\.0\.\d+|172\.23\.112\.\d+|localhost)(:\d+)?",  # 동일 네트워크 대역 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Session-Expires-In"],  # 커스텀 세션 TTL 헤더를 프론트에서 읽을 수 있도록 허용
)

app.state.sessions = {}

# 라우터 등록
app.include_router(router_auth)

# 회사 검색/등록 라우터
from WEB_SERVER.routers.router_company import router as router_company
app.include_router(router_company)

# 테넌트 관리 및 서비스 제공사 관리 라우터
from WEB_SERVER.routers.router_tenant import router as router_tenant
from WEB_SERVER.routers.router_system_admin import router as router_system_admin

app.include_router(router_tenant)
app.include_router(router_system_admin)