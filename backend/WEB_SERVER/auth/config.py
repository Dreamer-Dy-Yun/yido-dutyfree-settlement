###########################################
# Module name : config.py
# Module functions : 인증 관련 설정
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Supported by : Chat GPT-4o / Cursor AI
# Note : JWT, 비밀번호 해싱, OAuth2 설정
############################################

import os
from collections.abc import Mapping
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 스키마 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# JWT 설정
DEFAULT_JWT_SECRET_KEY = "your-secret-key-change-this-in-production"


def _is_production_env(env: Mapping[str, str] | None = None) -> bool:
    env_source = os.environ if env is None else env
    return any(
        str(env_source.get(key, "")).lower() in {"prod", "production"}
        for key in ("APP_ENV", "ENV", "ENVIRONMENT")
    )


def _resolve_secret_key(env: Mapping[str, str] | None = None) -> str:
    env_source = os.environ if env is None else env
    secret_key = env_source.get("JWT_SECRET_KEY", DEFAULT_JWT_SECRET_KEY)
    if _is_production_env(env_source) and secret_key in {"", DEFAULT_JWT_SECRET_KEY}:
        raise RuntimeError("JWT_SECRET_KEY must be set to a non-default value in production.")
    return secret_key


SECRET_KEY = _resolve_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Google OAuth 설정
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:10000/api/auth/google/callback")
GOOGLE_SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]
