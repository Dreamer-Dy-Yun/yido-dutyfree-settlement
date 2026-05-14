# DATABASE

`DATABASE` owns SQLAlchemy models, PostgreSQL DB manager setup, repository access, DB initialization, seed data, and DB tests.

## Files

| Path | Responsibility |
| --- | --- |
| `config.py` | Creates the process-wide `PGDBManager` and repository singletons from environment variables. |
| `setup_db.py` | Creates public schema tables during server startup. |
| `seed_data.py` | Optional initial seed-data helpers. Currently not invoked by default setup. |
| `initial_setting.txt` | Manual/legacy setup note. |
| `test.py` | Manual DB test/experiment file. Not part of pytest collection by default. |
| `__init__.py` | Database package exports. |

## Subfolders

| Path | Responsibility |
| --- | --- |
| `dbms/` | DB manager interface and concrete PostgreSQL implementation. |
| `models/` | SQLAlchemy declarative models for public and tenant schemas. |
| `repositories/` | Repository layer for authority/public data access. |
| `tests/` | DB manager and PostgreSQL behavior tests. Integration tests require `RUN_DB_TESTS=1`. |
| `temp/` | Local/manual SQL notes. Not an application contract. |

## Boundary Notes

- DB constraints are the source of truth for FK, unique, and nullability rules.
- Schema changes must update models, migration/setup expectations, and relevant README files.
- `DATABASE/dbms/postgre/pg_manager.py` is a hardened protection target. Do not refactor it for line-count reasons.
