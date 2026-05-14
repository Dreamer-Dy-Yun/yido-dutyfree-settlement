# Tenant API

Tenant management APIs live here.

| File | Responsibility |
| --- | --- |
| `tenantApi.js` | Public re-export for tenant user and usage APIs. |
| `tenantUsersApi.js` | Tenant user CRUD, activation, deletion, and password reset API functions. |
| `tenantUsageApi.js` | Tenant usage and per-user token usage API functions. |

## Boundary

- Data-mapping endpoints belong in `src/api/data-mapping/`, not here.
