# API

All browser-to-backend calls live behind this folder. Pages, hooks, and UI components should import domain functions from the matching API boundary instead of creating axios or fetch calls directly.

| Path | Responsibility |
| --- | --- |
| `client/` | Shared axios clients, auth header injection, session TTL updates, and 401 handling. |
| `auth/` | Login/logout, current-user/profile APIs, token/session storage, and selected tenant persistence. |
| `tenant/` | Tenant user and usage APIs. |
| `data-mapping/` | Tenant data-mapping APIs including uploads, OCR review, verification, matching, and EDI unified checks. |
| `admin/` | System-admin dashboard, tenant, service-account, LLM API key, and prompt APIs. |

## Boundary

- UI code imports API functions from the domain folder that owns the backend contract.
- `client/` is the only place that creates axios clients.
- Token/session persistence is kept in `auth/` so tests can mock the auth boundary.
- Login tenant selection persistence is kept in `auth/` instead of directly touching `localStorage` from pages.
- API functions return backend response data without inventing missing business values.
- Test files live beside the boundary they protect.
