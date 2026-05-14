# PROCESSOR_DATA/parsers

This folder contains vendor-specific EDI parser implementations.

## Files

| Path | Responsibility |
| --- | --- |
| `edi_lotte.py` | Lotte EDI parser and unified-field mapping. |
| `edi_silla.py` | Silla EDI parser and unified-field mapping. |
| `__init__.py` | Parser package marker. |

## Boundary Notes

- Keep vendor-specific column cleanup inside the relevant parser.
- Shared parser lifecycle belongs in `PROCESSOR_DATA/edi_processor.py`.
- If a vendor file contract changes, update parser tests and this README.
