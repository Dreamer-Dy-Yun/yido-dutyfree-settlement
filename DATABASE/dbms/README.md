# DATABASE/dbms

This folder defines the DB manager abstraction and DBMS-specific implementations.

## Files

| Path | Responsibility |
| --- | --- |
| `db_manager.py` | Abstract `DBManager` contract for batch upsert/update, DataFrame upsert/update, raw query execution, session handling, table lifecycle, and value conversion. |
| `postgre/` | PostgreSQL implementation of the DB manager contract. |
| `__init__.py` | Re-exports DBMS contracts/implementations. |

## Boundary Notes

- Application code should type against `DBManager` when possible.
- Concrete PostgreSQL behavior belongs under `postgre/`.
- Any signature change in `DBManager` is a cross-cutting API change and must update callers and tests.
