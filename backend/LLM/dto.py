from typing import List, Optional, Dict, Any
from pydantic import BaseModel, model_validator


class Message(BaseModel):
    """대화 히스토리 메시지"""
    role: str  # "user" | "assistant" | "system"
    content: str


class ToolFunction(BaseModel):
    """Function Calling용 함수 정의"""
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class Tool(BaseModel):
    """Function Calling용 도구"""
    type: str = "function"
    function: ToolFunction


class LLMRequest(BaseModel):
    prompt_system: str
    data: Optional[bytes] = None  
    mime_type: Optional[str] = None  
    prompt_user: Optional[str] = None  
    history: Optional[List[Message]] = None  # 대화 히스토리 (assistant + user)
    tools: Optional[List[Tool]] = None  # Function Calling용
    
    @model_validator(mode='after')
    def validate(self):
        if self.data and not self.mime_type:
            raise ValueError("mime_type is required when data is provided")
        if self.mime_type and not self.data:
            raise ValueError("data is required when mime_type is provided")
        if not self.prompt_user and not self.data:
            raise ValueError("At least one of prompt_user or data must be provided")
        return self


class LLMUsage(BaseModel):
    """토큰 사용량 정보"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMResponse(BaseModel):
    content: Dict[str, Any]  # JSON 파싱된 딕셔너리
    model: str | None = None
    usage: Optional[LLMUsage] = None
    finish_reason: str | None = None
    start_time: Optional[float] = None  # 요청 시작 시간 (Unix timestamp)

    