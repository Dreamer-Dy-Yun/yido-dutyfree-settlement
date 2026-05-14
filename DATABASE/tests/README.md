# DATABASE/tests

This folder contains DB manager tests.

## Files

| Path | Responsibility |
| --- | --- |
| `test_pgmanager_unique_keys_cases.py` | Unit coverage for unique/PK/conflict key selection behavior. |
| `test_pgmanager_upsert_testmodel.py` | Upsert behavior against `TestModel`; requires DB integration when enabled. |
| `test_pgmanager_update_testmodel.py` | Update behavior against `TestModel`; requires DB integration when enabled. |
| `test_pgmanager_integration.py` | PostgreSQL schema/table/session integration coverage. |
| `test_pgmanager.py` | Manual/integration table creation coverage. |
| `test_convert_datetime_for_db.py` | Manual datetime conversion test helper. |

## Execution

By default, integration tests are skipped unless `RUN_DB_TESTS=1`.

```bash
..\venv\Scripts\python.exe -m pytest -q
```
