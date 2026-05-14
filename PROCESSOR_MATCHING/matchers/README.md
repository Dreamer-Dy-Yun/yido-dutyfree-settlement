# PROCESSOR_MATCHING/matchers

This folder contains concrete receipt-passport matcher implementations.

## Files

| Path | Responsibility |
| --- | --- |
| `matcher_lotte.py` | Lotte-specific passport-receipt matching strategy. |
| `matcher_silla.py` | Silla-specific passport-receipt matching strategy. |
| `__init__.py` | Matcher package marker. |

## Boundary Notes

- Shared locking/fetching/flushing behavior belongs in `PROCESSOR_MATCHING/matcher.py`.
- Vendor-specific ranking and field comparison belong in the concrete matcher.
