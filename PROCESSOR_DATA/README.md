# PROCESSOR_DATA

This folder owns EDI parsing, vendor-specific normalization, EDI unified synchronization/export, and the Redis-backed EDI worker.

## Files

| Path | Responsibility |
| --- | --- |
| `edi_processor.py` | Abstract EDI processor contract. Hardened candidate for parser lifecycle and unified output shape. |
| `edi_unified_service.py` | Synchronizes parsed vendor EDI data into `EDI_Unified` and fills receipt/passport mappings. |
| `edi_unified_export.py` | Builds EDI unified export data for API download responses. |
| `patch.py` | XLSX repair helper for invalid datetime values. |
| `run_edi_unified_worker.py` | Redis worker that consumes EDI unified jobs and calls the internal tenant API. |
| `test_parser.py` | Parser tests for Lotte and Silla sample files. |
| `__init__.py` | Processor package marker. |

## Subfolders

| Path | Responsibility |
| --- | --- |
| `parsers/` | Vendor-specific EDI parsers. |
| `testdata/` | Sample Excel files used by parser tests. |

## Boundary Notes

- Vendor parsers should convert source-specific columns into stable unified columns.
- API upload routes may call parsers, but new parsing rules belong here.
- Worker code should enqueue/call internal APIs rather than duplicating DB mutation logic.
