# Auth API

Authentication, current-user, profile, token/session, and login tenant selection code lives here.

| File | Responsibility |
| --- | --- |
| `authApi.js` | Company search/registration, login/logout, current-user/profile, and password API functions. |
| `authTokenStore.js` | Browser token storage, JWT payload decoding, and post-login redirect decisions. |
| `tenantSelectionStore.js` | Last selected tenant company persistence for the login flow. |
| `sessionTtlStore.js` | In-memory session TTL store updated from API response headers. |
| `authTokenStore.test.js` | Token storage, JWT decoding, and redirect tests. |
| `tenantSelectionStore.test.js` | Selected tenant persistence tests. |

## Boundary

- Pages should not parse JWTs or read token-related `localStorage` keys directly.
- Client interceptors may import token/session utilities from this folder.
