import pytest
from pydantic import ValidationError

from LLM.dto import LLMRequest, Message, Tool, ToolFunction


def test_llm_request_accepts_text_prompt():
    request = LLMRequest(prompt_system="system", prompt_user="hello")

    assert request.prompt_system == "system"
    assert request.prompt_user == "hello"
    assert request.data is None


def test_llm_request_requires_user_prompt_or_data():
    with pytest.raises(ValidationError, match="At least one of prompt_user or data must be provided"):
        LLMRequest(prompt_system="system")


def test_llm_request_requires_mime_type_with_data():
    with pytest.raises(ValidationError, match="mime_type is required when data is provided"):
        LLMRequest(prompt_system="system", data=b"image-bytes")


def test_llm_request_requires_data_with_mime_type():
    with pytest.raises(ValidationError, match="data is required when mime_type is provided"):
        LLMRequest(prompt_system="system", mime_type="image/png")


def test_llm_request_keeps_history_and_tools_contract():
    request = LLMRequest(
        prompt_system="system",
        prompt_user="run",
        history=[Message(role="assistant", content="previous")],
        tools=[
            Tool(
                function=ToolFunction(
                    name="lookup",
                    description="Lookup data",
                    parameters={"type": "object"},
                )
            )
        ],
    )

    assert request.history[0].role == "assistant"
    assert request.tools[0].type == "function"
    assert request.tools[0].function.name == "lookup"
