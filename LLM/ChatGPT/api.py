########################################################
# ChatGPT API 구현체
# 
# 
# 
# 
# 
# 
# 
########################################################

from __future__ import annotations

import base64
import json
import time
from typing import Optional, Any, AsyncGenerator
import logging
import httpx

from ..llm import LLM
from ..dto import LLMRequest, LLMResponse, LLMUsage
from ..exceptions import LLMError, LLMAuthenticationError


logger = logging.getLogger(__name__)


class ChatGPT(LLM):
    """OpenAI ChatGPT API 구현체"""
    DEFAULT_MODEL = "gpt-4o"
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_TIMEOUT = 60.0
    DEFAULT_TEMPERATURE = 0.5
    DEFAULT_MAX_TOKENS = 1000

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        if not api_key:
            raise LLMAuthenticationError("API key is required")
        if httpx is None:
            raise ImportError("httpx is required for ChatGPT. Install it with: pip install httpx")
        
        super().__init__(api_key, model, base_url, timeout, temperature, max_tokens)
        self._client: Optional[httpx.AsyncClient] = None


    def _build_payload(self, request: LLMRequest, stream: bool = False) -> dict[str, Any]:
        """API 요청 payload 생성"""
        payload = {
            "model": self.model,
            "messages": self._convert_request_to_messages(request),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            **({"stream": True} if stream else {})
        }
        
        if request.tools:
            payload["tools"] = [tool.model_dump() for tool in request.tools]
        
        return payload

    async def _get_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 가져오기 (지연 초기화)"""
        if self._client is None or self._closed:
            self._check_closed()
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self._client

    def _to_json(self, content: str) -> dict[str, Any]:
        """마크다운 코드 블록 제거 후 JSON 파싱"""
        if not content or not content.strip():
            return {}
        
        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 1)[1]
            raw = raw.rsplit("```", 1)[0]
            
            lines = raw.split("\n")
            if lines and lines[0].strip() in ("json", "JSON"):
                raw = "\n".join(lines[1:])
        
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}\nContent: {raw[:500]}")
            return {}

    def _convert_request_to_messages(self, request: LLMRequest) -> list[dict[str, Any]]:
        """LLMRequest를 OpenAI messages 형식으로 변환"""
        messages: list[dict[str, Any]] = []
        
        if request.prompt_system:
            messages.append({"role": "system", "content": request.prompt_system})
        
        if request.history:
            messages.extend({"role": msg.role, "content": msg.content} for msg in request.history)

        content_parts: list[dict[str, Any]] = []

        if request.prompt_user:
            content_parts.append({"type": "text", "text": request.prompt_user})
        
        if request.data:
            image_data = base64.b64encode(request.data).decode('utf-8')
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:{request.mime_type};base64,{image_data}"}
            })
        
        if content_parts:
            messages.append({"role": "user", "content": content_parts})
            
        return messages


    async def ask(self, request: LLMRequest) -> LLMResponse:
        """ChatGPT API 호출"""
        self._check_closed()
        
        start_time = time.time()  # 요청 시작 시간 기록
        
        try:
            client = await self._get_client()
            payload = self._build_payload(request)
            
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            choice = data["choices"][0]
            message = choice["message"]
            
            usage_data = data.get("usage")
            usage = None
            if usage_data:
                usage = LLMUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0)
                )
            
            # 마크다운 코드 블록 제거 후 JSON 파싱
            content_str = message.get("content", "")
            if not content_str:
                logger.warning("Empty content in API response")
            content = self._to_json(content_str) if content_str else {}
            
            # content가 비어있으면 원본 응답 로깅
            if not content and content_str:
                logger.warning(f"Failed to parse content. Original response: {content_str[:1000]}")
            
            return LLMResponse(
                content=content,
                model=data.get("model"),
                usage=usage,
                finish_reason=choice.get("finish_reason"),
                start_time=start_time
            )
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.RequestError) as e:
            self._handle_http_error(e)
        except Exception as e:
            logger.error(f"Unexpected error in ChatGPT.ask: {e}", exc_info=True)
            raise LLMError(f"Unexpected error: {str(e)}")


    # TODO : 테스트등 필요한 부분 있을 수 있음(AI 작성분)
    async def ask_stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """ChatGPT 스트리밍 응답"""
        self._check_closed()
        
        try:
            client = await self._get_client()
            payload = self._build_payload(request, stream=True)
            
            async with client.stream("POST", "/chat/completions", json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if not line.strip() or not line.startswith("data: "):
                        continue
                    
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            content = choices[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.RequestError) as e:
            self._handle_http_error(e)
        except Exception as e:
            logger.error(f"Unexpected error in ChatGPT.ask_stream: {e}", exc_info=True)
            raise LLMError(f"Unexpected error: {str(e)}")

    async def close(self) -> None:
        """리소스 정리"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        await super().close()
