# PROCESSOR_MATCHING/tests

This folder contains matching integration coverage.

## Files

| Path | Responsibility |
| --- | --- |
| `test_matching_e2e.py` | End-to-end matching test using tenant/public schemas and DB state. |

## Execution

This test is skipped by default unless `RUN_DB_TESTS=1` because it requires local DB/Redis/schema setup.
