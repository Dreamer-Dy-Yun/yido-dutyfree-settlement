###########################################
# Module name : __init__.py
# Module functions : auth 모듈 export
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Supported by : Chat GPT-4o / Cursor AI
# Note : 
############################################

# 설정
from WEB_SERVER.auth.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    oauth2_scheme,
    pwd_context
)

# JWT
from WEB_SERVER.auth.jwt import (
    create_access_token,
    decode_token
)

# 비밀번호
from WEB_SERVER.auth.password import (
    verify_password,
    get_password_hash
)

# 의존성
from WEB_SERVER.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    check_permission,
    require_permission
)

# Google OAuth
from WEB_SERVER.auth.google_oauth import (
    get_google_authorization_url,
    generate_state_token,
    get_google_user_info,
    verify_google_token
)

__all__ = [
    # 설정
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "oauth2_scheme",
    "pwd_context",
    # JWT
    "create_access_token",
    "decode_token",
    # 비밀번호
    "verify_password",
    "get_password_hash",
    # 의존성
    "get_current_user",
    "get_current_active_user",
    "get_current_superuser",
    "check_permission",
    "require_permission",
    # Google OAuth
    "get_google_authorization_url",
    "generate_state_token",
    "get_google_user_info",
    "verify_google_token",
]
