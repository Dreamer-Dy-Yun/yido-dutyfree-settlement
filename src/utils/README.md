# Utils

Small shared frontend utility functions live here.

| File | Responsibility |
| --- | --- |
| `normalizeApiError.js` | Converts axios/FastAPI error details into user-facing text. |
| `userFeedback.js` | Browser notification and confirmation boundary. |
| `userFeedback.test.js` | Tests for the user feedback boundary. |
| `dateFormat.js` | Korean locale date/time formatting helpers. |
| `dateFormat.test.js` | Date formatting helper tests. |

## Boundary

- Utilities must not own React state or call backend APIs.
- Browser APIs that are still globally backed, such as alert/confirm, should be wrapped here before UI components use them.
