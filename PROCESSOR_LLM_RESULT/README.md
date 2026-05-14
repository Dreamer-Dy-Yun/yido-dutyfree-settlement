# PROCESSOR_LLM_RESULT

This folder owns OCR execution over image records and parsing of LLM OCR responses into DB-ready data.

## Files

| Path | Responsibility |
| --- | --- |
| `image_ocr_runner.py` | Loads unprocessed images, calls configured LLM, parses results, updates image/OCR/usage tables. |
| `yido_parser.py` | Parses LLM response JSON into receipt, passport, and usage DataFrames. |
| `tests/` | Unit tests for OCR result parsing contracts. |

## Boundary Notes

- LLM API calls go through `LLM/` abstractions.
- DB writes go through `DBManager`.
- Prompt/API-key resolution belongs in `WEB_SERVER/services/service_image_ocr.py`, not in this processor.
