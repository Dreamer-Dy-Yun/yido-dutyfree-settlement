# API

All browser-to-backend calls live behind this folder. Pages, hooks, and UI components should import domain functions from here instead of creating axios or fetch calls directly.

| File | Responsibility |
| --- | --- |
| `client.js` | Shared tenant/admin axios clients, auth header injection, session TTL updates, and 401 handling. |
| `authTokenStore.js` | Browser token storage and JWT payload decoding helpers. |
| `authTokenStore.test.js` | Token storage, JWT decoding, and post-login redirect tests. |
| `tenantSelectionStore.js` | Last selected tenant company persistence for the login flow. |
| `tenantSelectionStore.test.js` | Selected tenant persistence tests. |
| `sessionTtlStore.js` | In-memory session TTL store updated from API response headers. |
| `authApi.js` | Company registration, login/logout, current-user, profile, and password API functions. |
| `tenantApi.js` | Tenant user, usage, image upload/review/verify, and image matching API functions. |
| `ediUnifiedApi.js` | EDI unified job, group listing/detail, and Excel export API functions. |
| `systemAdminApi.js` | System admin dashboard, tenant, service-account, LLM API key, and prompt API functions. |

## Boundary

- UI code imports API functions from this folder only.
- Token/session persistence is kept inside API utilities so tests can mock this folder as a single boundary.
- Login tenant selection persistence is kept here instead of directly touching `localStorage` from pages.
- API functions return backend response data without inventing missing business values.
- Test files in this folder protect browser storage and auth/session decisions from page-level regressions.
