# CUSTOMIZED

This folder contains shared utility modules used across the backend.

## Files

| Path | Responsibility |
| --- | --- |
| `cust_converter.py` | String/enum conversion helpers. |
| `cust_deco_error.py` | Error-handling and query-param decorator helpers used by routes. |
| `cust_deco_retry.py` | Async retry decorator helper. |
| `cust_excel_processor.py` | Excel processing utilities. |
| `cust_hasher.py` | Hashing helpers for strings, bytes, files, dict JSON payloads, and comparisons. |
| `cust_iterator.py` | Iterator helper utilities. |
| `cust_linux.py` | Linux command/helper utilities. |
| `cust_logger.py` | Shared logger configuration. |
| `cust_parser.py` | Generic parser helpers. |
| `cust_powershell.py` | PowerShell expression/builder helpers. |
| `cust_retrier.py` | Retry workflow helper class. |
| `cust_validator.py` | Validation and guard helpers. |
| `cust_web_helper.py` | Web/export helpers, especially Excel streaming/template export. |
| `cust_zip_processor.py` | ZIP extraction and saved-file metadata helper. |
| `__init__.py` | Utility package marker. |

## Subfolders

| Path | Responsibility |
| --- | --- |
| `tests/` | Utility tests. |

## Boundary Notes

- Utilities should remain domain-agnostic where possible.
- Domain logic for EDI/OCR/matching should stay in the relevant processor/service folder.
