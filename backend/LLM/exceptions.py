from __future__ import annotations


class LLMError(Exception):
    """LLM 관련 기본 예외 클래스"""
    pass


class LLMAPIError(LLMError):
    """API 호출 실패 예외"""
    pass


class LLMAuthenticationError(LLMError):
    """인증 실패 예외 (API 키 오류 등)"""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit 초과 예외"""
    pass


class LLMTimeoutError(LLMError):
    """타임아웃 예외"""
    pass
