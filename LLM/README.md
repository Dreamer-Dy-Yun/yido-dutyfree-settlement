# LLM

This folder owns the LLM provider abstraction, request/response DTOs, exceptions, and provider-specific implementations.

## Files

| Path | Responsibility |
| --- | --- |
| `llm.py` | Abstract LLM interface and lifecycle contract. Hardened candidate. |
| `dto.py` | Pydantic DTOs for messages, tools, requests, usage, and responses. Hardened candidate. |
| `exceptions.py` | LLM-specific exception hierarchy. |

## Subfolders

| Path | Responsibility |
| --- | --- |
| `ChatGPT/` | ChatGPT/OpenAI-compatible implementation of the LLM interface. |
| `prompt/` | Prompt text files used during OCR/LLM experiments or setup. |

## Boundary Notes

- Provider-specific HTTP behavior belongs in provider subfolders.
- OCR/business parsing belongs in `PROCESSOR_LLM_RESULT`, not in DTOs.
- Do not hardcode active prompt/API-key selection here; that is DB/service configuration.
