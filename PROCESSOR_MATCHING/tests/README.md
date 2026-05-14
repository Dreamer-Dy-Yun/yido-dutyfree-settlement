# PROCESSOR_MATCHING/tests

This folder contains matching integration coverage.

## Files

| Path | Responsibility |
| --- | --- |
| `test_matching_e2e.py` | End-to-end matching test using tenant/public schemas and DB state. |

## Execution

This test is not collected by default because it requires local DB/Redis/schema setup.

```bash
..\venv\Scripts\python.exe -m pytest -q --run-db-tests PROCESSOR_MATCHING/tests
```
