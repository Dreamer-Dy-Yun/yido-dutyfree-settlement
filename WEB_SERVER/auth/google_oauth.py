###########################################
# Module name : google_oauth.py
# Module functions : Google OAuth 인증 로직
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Supported by : Chat GPT-4o / Cursor AI
# Note : Google OAuth 2.0 인증 플로우 처리
############################################

import secrets
from typing import Optional
from fastapi import HTTPException, status
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from WEB_SERVER.auth.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES
)


def create_google_flow() -> Flow:
    """Google OAuth Flow 생성"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth 설정이 완료되지 않았습니다. GOOGLE_CLIENT_ID와 GOOGLE_CLIENT_SECRET을 설정해주세요."
        )
    
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [GOOGLE_REDIRECT_URI]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    
    return flow


def generate_state_token() -> str:
    """CSRF 방지를 위한 state 토큰 생성"""
    return secrets.token_urlsafe(32)


def get_google_authorization_url(state: str) -> str:
    """Google 인증 URL 생성"""
    flow = create_google_flow()
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=state,
        prompt="consent"
    )
    return authorization_url


async def verify_google_token(token: str) -> dict:
    """Google ID 토큰 검증 및 사용자 정보 추출"""
    try:
        # Google ID 토큰 검증
        idinfo = id_token.verify_oauth2_token(
            token,
            Request(),
            GOOGLE_CLIENT_ID
        )
        
        # 토큰 발급자 확인
        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Wrong issuer.")
        
        return {
            "email": idinfo.get("email"),
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture"),
            "sub": idinfo.get("sub"),  # Google 사용자 고유 ID
            "email_verified": idinfo.get("email_verified", False)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google 토큰 검증 실패: {str(e)}"
        )


async def get_google_user_info(code: str, state: str) -> dict:
    """Google OAuth 콜백에서 사용자 정보 가져오기"""
    flow = create_google_flow()
    
    try:
        # 인증 코드를 액세스 토큰으로 교환
        flow.fetch_token(code=code)
        
        # 사용자 정보 가져오기
        credentials = flow.credentials
        idinfo = id_token.verify_oauth2_token(
            credentials.id_token,
            Request(),
            GOOGLE_CLIENT_ID
        )
        
        # 토큰 발급자 확인
        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Wrong issuer.")
        
        return {
            "email": idinfo.get("email"),
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture"),
            "sub": idinfo.get("sub"),  # Google 사용자 고유 ID
            "email_verified": idinfo.get("email_verified", False)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google 인증 실패: {str(e)}"
        )
