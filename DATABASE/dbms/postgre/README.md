# DATABASE/dbms/postgre

This folder contains the PostgreSQL implementation of the backend DB manager contract.

## Files

| Path | Responsibility |
| --- | --- |
| `pg_manager.py` | Public facade. Exports `PGDBManager` and re-exports `DataBaseMaker`; owns engine/session factory initialization and raw query execution. |
| `pg_database.py` | `DataBaseMaker`: development/test database existence check and database creation. |
| `pg_schema.py` | Schema search-path, schema lifecycle, table create/drop/copy, and truncate behavior. |
| `pg_batch.py` | DataFrame batch `upsert`/`update`, statement generation, batch transaction result handling, and legacy `_upsert_dataframe` wrapper. |
| `pg_batch_executor.py` | Shared batch execution loop, partial-commit result assembly, and batch error formatting. |
| `pg_dataframe.py` | DataFrame value conversion based on SQLAlchemy model column types. |
| `pg_constraints.py` | SQLAlchemy metadata inspection for PK/UK/FK, nullability, and conflict-key selection. |
| `pg_identifiers.py` | PostgreSQL identifier quoting helpers for schema, table, database, and search-path SQL. |
| `lagacy/pg_manager.py` | Intentional pre-refactor snapshot restored from Git HEAD. This is outside the active modification scope and exists only to preserve the original shape for reference. Do not import from runtime code. |
| `__init__.py` | PostgreSQL DBMS package marker/export surface. |

## Hardening Status

This package is treated as a hardened protection target.

Do not refactor or simplify these modules without explicit user approval. The public surface remains `DATABASE.dbms.postgre.pg_manager.PGDBManager`; the split modules are private responsibility units behind that facade.

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
- `partial_commit=True`: successful batches are committed, failed batches are rolled back and returned in the result with `errors`.
- `partial_commit=False` or injected sessions: commit/rollback ownership stays with the caller and failures raise.
- Schema/table/database names must pass through `pg_identifiers.py`; direct f-string identifier interpolation is outside the contract.

## Verification Evidence

Existing tests cover the core behavior:

- `DATABASE/tests/test_pgmanager_unique_keys_cases.py`
- `DATABASE/tests/test_pgmanager_upsert_testmodel.py`
- `DATABASE/tests/test_pgmanager_update_testmodel.py`
- `DATABASE/tests/test_pgmanager_integration.py`
- `DATABASE/tests/test_pgmanager.py`

Integration coverage requires `RUN_DB_TESTS=1` and a local PostgreSQL/Redis/schema environment.
