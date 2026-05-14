###########################################
# Module name : verification_token.py
# Module functions : 이메일 인증 토큰 생성 및 관리
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.01.30
# Supported by : Cursor AI
# Note : 회원가입 이메일 인증 토큰 관리
############################################

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from WEB_SERVER.auth.redis_session import session_manager
from CUSTOMIZED.cust_logger import logger


class VerificationTokenService:
    """이메일 인증 토큰 서비스"""
    
    def __init__(self):
        self.token_expire_hours = 24  # 토큰 유효기간 24시간
    
    def generate_token(self, email: str) -> str:
        """인증 토큰 생성"""
        # 랜덤 토큰 생성
        random_token = secrets.token_urlsafe(32)
        
        # 이메일과 결합하여 고유한 토큰 생성
        token_data = f"{email}:{random_token}:{datetime.now().isoformat()}"
        token = hashlib.sha256(token_data.encode()).hexdigest()
        
        return token
    
    def save_token(self, email: str, token: str, user_id: int) -> bool:
        """토큰을 Redis에 저장"""
        try:
            expire_seconds = self.token_expire_hours * 3600  # 24시간을 초로 변환
            
            # Redis에 토큰 저장 (key: verification_token:{token})
            session_manager.redis_client.setex(
                f"verification_token:{token}",
                expire_seconds,
                f"{email}:{user_id}"
            )
            
            logger.info(f"인증 토큰 저장 완료: {email}")
            return True
            
        except Exception as e:
            logger.error(f"인증 토큰 저장 실패: {e}")
            return False
    
    def verify_token(self, token: str) -> Optional[dict]:
        """토큰 검증 및 사용자 정보 반환"""
        try:
            # Redis에서 토큰 조회
            token_data = session_manager.redis_client.get(f"verification_token:{token}")
            
            if not token_data:
                logger.warning(f"유효하지 않은 토큰 또는 만료된 토큰: {token}")
                return None
            
            # 토큰 데이터 파싱 (email:user_id 형식)
            email, user_id = token_data.decode('utf-8').split(':')
            
            return {
                'email': email,
                'user_id': int(user_id)
            }
            
        except Exception as e:
            logger.error(f"토큰 검증 실패: {e}")
            return None
    
    def delete_token(self, token: str) -> bool:
        """토큰 삭제 (인증 완료 후)"""
        try:
            session_manager.redis_client.delete(f"verification_token:{token}")
            logger.info(f"인증 토큰 삭제 완료: {token}")
            return True
        except Exception as e:
            logger.error(f"토큰 삭제 실패: {e}")
            return False


# 싱글톤 인스턴스
verification_token_service = VerificationTokenService()
