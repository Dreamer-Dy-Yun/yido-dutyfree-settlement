# PROCESSOR_IMAGE

This folder contains image helper and experimental code.

## Files

| Path | Responsibility |
| --- | --- |
| `rate_limiter.py` | Async byte-rate limiter helper for image or stream processing. |
| `ttt.py` | Local image helper/experiment. Confirm usage before extending. |

## Boundary Notes

- Production OCR workflow currently lives in `PROCESSOR_LLM_RESULT` and `WEB_SERVER/services/service_image_ocr.py`.
- Treat files here as helper/POC code unless a caller proves production use.
