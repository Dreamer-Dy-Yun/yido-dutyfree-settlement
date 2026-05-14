# API Client

Shared axios client setup lives here.

| File | Responsibility |
| --- | --- |
| `apiClient.js` | Tenant/admin axios clients, authorization header injection, TTL updates, and authenticated 401 redirects. |

## Boundary

- This folder is the only API layer location that creates axios instances.
- Domain API folders import `tenantApiClient` or `adminApiClient` from here.
