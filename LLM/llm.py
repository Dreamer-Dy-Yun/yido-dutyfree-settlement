from __future__ import annotations

from abc import ABC, abstractmethod
import logging
import httpx

from .dto import LLMResponse, LLMRequest
from .exceptions import (
    LLMError,
    LLMAuthenticationError,
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError
)


logger = logging.getLogger(__name__)


class LLM(ABC):

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float = 60.0, temperature: float = 0.5, max_tokens: int = 1000):
        self.api_key: str = api_key
        self.model: str = model
        self.base_url: str = base_url
        self.timeout: float = timeout
        self.temperature: float = temperature
        self.max_tokens: int = max_tokens
        self._closed: bool = False

    @abstractmethod
    async def ask(self, request: LLMRequest) -> LLMResponse:
        pass

    async def ask_stream(self, request: LLMRequest):
        """스트리밍 응답을 위한 제너레이터 메서드 (선택적 구현)"""
        raise NotImplementedError("Streaming is not supported by this LLM implementation")

    async def close(self) -> None:
        """리소스 정리"""
        self._closed = True

    async def __aenter__(self):
        """비동기 context manager 진입"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 context manager 종료"""
        await self.close()

    def __enter__(self):
        """동기 context manager 진입 (비동기 객체이므로 경고)"""
        logger.warning("Using synchronous context manager with async LLM. Use 'async with' instead.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """동기 context manager 종료"""
        pass

    def _check_closed(self) -> None:
        """닫힌 객체 사용 시도 시 예외 발생"""
        if self._closed:
            raise LLMError("LLM instance has been closed")

    def _handle_http_error(self, e: Exception) -> None:
        """HTTP 에러 처리 (httpx 에러를 LLM 예외로 변환)"""
        if httpx is None:
            raise LLMError(f"Request failed: {str(e)}")
        
        if isinstance(e, httpx.HTTPStatusError):
            status_code = e.response.status_code
            if status_code == 401:
                raise LLMAuthenticationError(f"Invalid API key: {e.response.text}")
            elif status_code == 429:
                raise LLMRateLimitError(f"Rate limit exceeded: {e.response.text}")
            elif status_code in (408, 504):
                raise LLMTimeoutError(f"Request timeout: {e.response.text}")
            else:
                raise LLMAPIError(f"API error ({status_code}): {e.response.text}")
        elif isinstance(e, httpx.TimeoutException):
            raise LLMTimeoutError(f"Request timeout: {str(e)}")
        elif isinstance(e, httpx.RequestError):
            raise LLMAPIError(f"Request failed: {str(e)}")
        else:
            raise