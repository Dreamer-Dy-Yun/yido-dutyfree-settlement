import os
from fastapi import FastAPI
from WEB_SERVER.routers import router_root, router_pmf, router_similarity
from fastapi.middleware.cors import CORSMiddleware
from DATABASE.config import db_manager, apply_postgres_vector_scale_index

app = FastAPI(
    title="NOVAS EZ API",
    description="NOVAS EZ 프로젝트 FastAPI 예제",
    version="1.0.0"
)

# CORS 미들웨어 설정
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3001,http://192.168.0.19:3001,http://172.23.112.1:3001").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_origin_regex=r"http://(192\.168\.0\.\d+|172\.23\.112\.\d+|localhost)(:\d+)?",  # 동일 네트워크 대역 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.sessions = {}

# 라우터 등록
app.include_router(router_root)
app.include_router(router_pmf)
app.include_router(router_similarity)


@app.on_event("startup")
async def startup_event() -> None:
    """앱 시작 시 DB 테이블 및 인덱스 초기화"""
    await db_manager.create_tables()
    await apply_postgres_vector_scale_index(db_manager)