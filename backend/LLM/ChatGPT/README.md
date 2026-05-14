# LLM/ChatGPT

This folder contains the ChatGPT/OpenAI-compatible LLM provider implementation.

## Files

| Path | Responsibility |
| --- | --- |
| `api.py` | `ChatGPT` implementation for request payload creation, async HTTP calls, response parsing, streaming, and client close lifecycle. |

## Boundary Notes

- The class implements the `LLM` contract from `LLM/llm.py`.
- API keys and model names are injected by callers; do not resolve DB settings here.
