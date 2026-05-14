###########################################
# Module name : password.py
# Module functions : 비밀번호 해싱 및 검증
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Supported by : Chat GPT-4o / Cursor AI
# Note : 비밀번호 해싱/검증 유틸리티 (Hasher 클래스 사용)
############################################

from CUSTOMIZED.cust_hasher import Hasher


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증 (SHA-256 해시 비교)"""
    hasher = Hasher()
    hasher.hash(plain_password)
    return hasher.equals(hashed_password, is_hashed=True)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱 (SHA-256 hex 문자열 반환)"""
    hasher = Hasher()
    hasher.hash(password)
    return hasher.to_hex_string  # @property이므로 괄호 없이 사용
