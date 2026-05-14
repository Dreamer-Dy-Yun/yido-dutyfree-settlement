# DATABASE/dbms/postgre

This folder contains the PostgreSQL implementation of the backend DB manager contract.

## Files

| Path | Responsibility |
| --- | --- |
| `pg_manager.py` | `DataBaseMaker` and `PGDBManager`: PostgreSQL database/schema/table lifecycle, async engine/session handling, schema search path, query execution, DataFrame conversion, batch upsert/update, and metadata inspection. |
| `__init__.py` | PostgreSQL DBMS package marker/export surface. |

## Hardening Status

`pg_manager.py` is treated as a hardened protection target.

Do not split, refactor, or simplify it without explicit user approval, even though it exceeds the default 300-line guideline. It is a central infrastructure module with broad impact across routers, repositories, processors, and tests.

## Protected Contract

The following behavior is part of the protected contract:

- Engine initialization and connection pool settings from `DATABASE/config.py`.
- Async session lifecycle and transaction boundary behavior.
- PostgreSQL schema creation, deletion, existence checks, and search-path setup.
- Public/tenant table creation from SQLAlchemy metadata.
- `execute_query` behavior used by routers, services, repositories, processors, and tests.
- DataFrame conversion by SQLAlchemy model column type.
- Batch `upsert` and `update` conflict-key selection.
- Unique/PK/constraint inspection used to choose suitable conflict keys.

## Verification Evidence

Existing tests cover the core behavior:

- `DATABASE/tests/test_pgmanager_unique_keys_cases.py`
- `DATABASE/tests/test_pgmanager_upsert_testmodel.py`
- `DATABASE/tests/test_pgmanager_update_testmodel.py`
- `DATABASE/tests/test_pgmanager_integration.py`
- `DATABASE/tests/test_pgmanager.py`

Integration coverage requires `RUN_DB_TESTS=1` and a local PostgreSQL/Redis/schema environment.
