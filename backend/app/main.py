from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import auth, users
from app.core.exceptions import setup_exception_handlers

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 예외 핸들러 설정
setup_exception_handlers(app)

# API 라우터 등록
app.include_router(auth.router, prefix="/api/v1", tags=["인증"])
app.include_router(users.router, prefix="/api/v1", tags=["사용자"])


@app.get("/")
async def root():
    return {
        "message": "FastAPI Backend Template",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
