# Admin API

System-admin API contracts live here.

| File | Responsibility |
| --- | --- |
| `systemAdminApi.js` | System dashboard, tenant approval/deletion, service-account, LLM API key, and prompt API functions. |

## Boundary

- System-admin pages import backend functions from this folder.
- Tenant-user management APIs belong in `src/api/tenant/`.
