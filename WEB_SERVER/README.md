# WEB_SERVER

`WEB_SERVER` is the active FastAPI application layer. It owns HTTP routing, auth dependencies, request-level dependency injection, service orchestration, CORS setup, and the uvicorn entry point.

## Files

| Path | Responsibility |
| --- | --- |
| `app.py` | Creates the active FastAPI app, configures CORS and lifespan setup, registers active routers. |
| `main_web.py` | Uvicorn launcher for `WEB_SERVER.app:app`; also runs DB setup when executed directly. |
| `__init__.py` | Package marker. |

## Subfolders

| Path | Responsibility |
| --- | --- |
| `auth/` | OAuth2/JWT/password/session dependencies and Google OAuth helpers. |
| `routers/` | FastAPI route modules and router-local schemas/helpers. |
| `services/` | Business workflows used by routers and background jobs. |

## Active Router Registration

`app.py` registers:

- `router_auth`
- `router_company`
- `router_tenant`
- `router_system_admin`

`router_registration.py` is not registered. Do not treat `/api/registration/*` as active until `app.py` includes it or the contract is confirmed.

## Boundary Notes

- Keep request/response schemas close to the API domain, unless the schema is reused across routers.
- Keep direct DB access out of new large route handlers when a service boundary is more appropriate.
- When a route changes API behavior, update `WEB_SERVER/routers/README.md` and any frontend/API contract documentation that depends on it.
