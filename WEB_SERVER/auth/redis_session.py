###########################################
# Module name : redis_session.py
# Module functions : Redis를 사용한 세션 관리
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.01.27
# Updated at : 2025.01.27
# Supported by : Chat GPT-4o / Cursor AI
# Note : Redis를 사용한 JWT 토큰 세션 관리
############################################

import os
import redis
from typing import Optional
from datetime import timedelta
import json
try:
    import pandas as pd
except ImportError:
    pd = None

# Redis 연결 설정
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_SESSION_PREFIX = "session:"
REDIS_USER_SESSION_PREFIX = "user_session:"
REDIS_USER_SETTINGS_PREFIX = "user_settings:"  # 사용자별 설정 저장


def get_redis_client() -> redis.Redis:
    """Redis 클라이언트 생성"""
    try:
        return redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as e:
        raise ConnectionError(f"Redis 연결 실패: {e}")


class RedisSessionManager:
    """Redis를 사용한 세션 관리 클래스"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
    
    def create_session(
        self, 
        token: str, 
        user_id: int, 
        email: str,
        expires_in: int = 1800  # 기본 30분 (초 단위)
    ) -> bool:
        """
        세션 생성 (토큰을 Redis에 저장)
        
        Args:
            token: JWT 토큰
            user_id: 사용자 ID
            email: 사용자 이메일
            expires_in: 만료 시간 (초)
        
        Returns:
            bool: 성공 여부
        """
        try:
            # 토큰을 키로 사용하여 세션 정보 저장
            session_key = f"{REDIS_SESSION_PREFIX}{token}"
            session_data = {
                "user_id": user_id,
                "email": email,
                "token": token
            }
            
            # Redis에 저장 (TTL 설정)
            self.redis_client.setex(
                session_key,
                expires_in,
                json.dumps(session_data)
            )
            
            # 사용자별 세션 목록 관리 (한 사용자가 여러 기기에서 로그인 가능)
            user_sessions_key = f"{REDIS_USER_SESSION_PREFIX}{user_id}"
            self.redis_client.sadd(user_sessions_key, token)
            self.redis_client.expire(user_sessions_key, expires_in)
            
            return True
        except Exception as e:
            print(f"세션 생성 실패: {e}")
            return False
    
    def get_session(self, token: str) -> Optional[dict]:
        """
        세션 조회
        
        Args:
            token: JWT 토큰
        
        Returns:
            dict: 세션 정보 또는 None
        """
        try:
            session_key = f"{REDIS_SESSION_PREFIX}{token}"
            session_data = self.redis_client.get(session_key)
            
            if session_data:
                return json.loads(session_data)
            return None
        except Exception as e:
            print(f"세션 조회 실패: {e}")
            return None
    
    def delete_session(self, token: str) -> bool:
        """
        세션 삭제 (로그아웃)
        
        Args:
            token: JWT 토큰
        
        Returns:
            bool: 성공 여부
        """
        try:
            # 세션 정보 조회
            session_data = self.get_session(token)
            if not session_data:
                return False
            
            user_id = session_data.get("user_id")
            
            # 토큰 세션 삭제
            session_key = f"{REDIS_SESSION_PREFIX}{token}"
            self.redis_client.delete(session_key)
            
            # 사용자 세션 목록에서도 제거
            if user_id:
                user_sessions_key = f"{REDIS_USER_SESSION_PREFIX}{user_id}"
                self.redis_client.srem(user_sessions_key, token)
            
            return True
        except Exception as e:
            print(f"세션 삭제 실패: {e}")
            return False
    
    def delete_all_user_sessions(self, user_id: int) -> bool:
        """
        사용자의 모든 세션 삭제 (강제 로그아웃)
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            bool: 성공 여부
        """
        try:
            user_sessions_key = f"{REDIS_USER_SESSION_PREFIX}{user_id}"
            tokens = self.redis_client.smembers(user_sessions_key)
            
            # 모든 토큰 세션 삭제
            for token in tokens:
                session_key = f"{REDIS_SESSION_PREFIX}{token}"
                self.redis_client.delete(session_key)
            
            # 사용자 세션 목록 삭제
            self.redis_client.delete(user_sessions_key)
            
            return True
        except Exception as e:
            print(f"사용자 세션 삭제 실패: {e}")
            return False
    
    def extend_session(self, token: str, expires_in: int = 1800) -> bool:
        """
        세션 만료 시간 연장
        
        Args:
            token: JWT 토큰
            expires_in: 연장할 시간 (초)
        
        Returns:
            bool: 성공 여부
        """
        try:
            session_data = self.get_session(token)
            if not session_data:
                return False
            
            session_key = f"{REDIS_SESSION_PREFIX}{token}"
            self.redis_client.expire(session_key, expires_in)
            
            # 사용자 세션 목록도 연장
            user_id = session_data.get("user_id")
            if user_id:
                user_sessions_key = f"{REDIS_USER_SESSION_PREFIX}{user_id}"
                self.redis_client.expire(user_sessions_key, expires_in)
            
            return True
        except Exception as e:
            print(f"세션 연장 실패: {e}")
            return False
    
    def is_session_valid(self, token: str) -> bool:
        """
        세션이 유효한지 확인
        
        Args:
            token: JWT 토큰
        
        Returns:
            bool: 유효 여부
        """
        return self.get_session(token) is not None
    
    def get_session_ttl(self, token: str) -> Optional[int]:
        """
        현재 세션의 TTL(남은 수명, 초 단위)을 조회
        
        Args:
            token: JWT 토큰
        
        Returns:
            Optional[int]: 남은 수명(초). 세션이 없거나 TTL 미지원 시 None
        """
        try:
            session_key = f"{REDIS_SESSION_PREFIX}{token}"
            ttl = self.redis_client.ttl(session_key)
            # Redis TTL 반환값:
            #  -2: key 없음, -1: 만료 시간 없음, 0 이상: 남은 TTL(초)
            if ttl is None or ttl < 0:
                return None
            return int(ttl)
        except Exception as e:
            print(f"세션 TTL 조회 실패: {e}")
            return None
    
    def get_user_token_expire_minutes(self, user_id: int, default: int = 30) -> int:
        """
        사용자별 토큰 유효기간 조회 (분 단위)
        
        Args:
            user_id: 사용자 ID
            default: 기본값 (분)
        
        Returns:
            int: 토큰 유효기간 (분)
        """
        try:
            settings_key = f"{REDIS_USER_SETTINGS_PREFIX}{user_id}"
            settings_json = self.redis_client.get(settings_key)
            
            if settings_json:
                settings = json.loads(settings_json)
                return settings.get("token_expire_minutes", default)
            return default
        except Exception as e:
            print(f"사용자 설정 조회 실패: {e}")
            return default
    
    def set_user_token_expire_minutes(self, user_id: int, expire_minutes: int) -> bool:
        """
        사용자별 토큰 유효기간 설정 (분 단위)
        
        Args:
            user_id: 사용자 ID
            expire_minutes: 토큰 유효기간 (분)
        
        Returns:
            bool: 성공 여부
        """
        try:
            settings_key = f"{REDIS_USER_SETTINGS_PREFIX}{user_id}"
            settings = {
                "token_expire_minutes": expire_minutes,
                "updated_at": str(pd.Timestamp.now()) if 'pd' in globals() else None
            }
            
            # 설정 저장 (만료 없음)
            self.redis_client.set(settings_key, json.dumps(settings))
            return True
        except Exception as e:
            print(f"사용자 설정 저장 실패: {e}")
            return False


# 전역 세션 매니저 인스턴스
session_manager = RedisSessionManager()
