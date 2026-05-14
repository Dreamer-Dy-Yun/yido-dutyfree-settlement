# DATABASE/repositories/authorities

This folder contains repositories for authority and account-related data.

## Files

| Path | Responsibility |
| --- | --- |
| `tenant_repository.py` | Tenant lookup/update/create helpers for public tenant records. |
| `user_repository.py` | Tenant user lookup/update/create helpers. |
| `__init__.py` | Authority repository exports. |

## Boundary Notes

- These repositories depend on `DBManager` and the SQLAlchemy models.
- Keep tenant-schema selection explicit in callers or repository methods.
