# DATABASE/repositories

This folder contains repository abstractions and concrete repository packages.

## Files

| Path | Responsibility |
| --- | --- |
| `base.py` | Base repository dependency on `DBManager`; contract point for repository implementations. |
| `authorities/` | Repositories for tenant and user authority data. |
| `__init__.py` | Repository package exports. |

## Boundary Notes

- Repositories should encapsulate repeated DB access patterns.
- Keep API request/response shaping in routers or services, not repositories.
- Repository contract changes must update dependency providers in `WEB_SERVER/routers/settings.py`.
