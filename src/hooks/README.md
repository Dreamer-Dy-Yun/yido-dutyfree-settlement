# Hooks

Shared React hooks live here.

| File | Responsibility |
| --- | --- |
| `useCurrentUser.js` | Loads the tenant current-user session for dashboard shell pages and exposes refresh behavior for profile updates. |
| `useSessionTTL.js` | Subscribes to session TTL changes captured from API responses. |

Hooks in this folder should not own page-specific rendering decisions. Keep feature-specific hooks inside the feature folder that owns the UI state.
