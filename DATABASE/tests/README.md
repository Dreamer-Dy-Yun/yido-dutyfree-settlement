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

By default, DB integration tests are not collected. This keeps the normal backend check focused on tests that can run without local PostgreSQL/Redis.

```bash
..\venv\Scripts\python.exe -m pytest -q
```

Collect and run DB integration tests only when the local DB environment is ready:

```bash
..\venv\Scripts\python.exe -m pytest -q --run-db-tests
```
