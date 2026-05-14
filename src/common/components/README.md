# Common Components

Cross-flow shared components live here.

| File | Responsibility |
| --- | --- |
| `ProtectedRoute.jsx` | Tenant/admin route guard and login redirect selection. |
| `ProtectedRoute.test.jsx` | Route guard tests for tenant and system-admin protected routes. |

## Boundary

- Components in this folder should not fetch backend data directly.
- Auth decisions are read through `src/api/authApi.js` so tests can mock the auth boundary.
