# Locales

UI display strings that are shared across components live here.

| File | Responsibility |
| --- | --- |
| `KO.ts` | Korean UI text constants. Components import this module instead of keeping repeated Korean literals inline. |

## Boundary

- This folder owns frontend presentation text only.
- API field names, backend enum values, and persisted business values must stay in the API/service layer or the calling feature module.
- Add new nested keys by feature area so a component can import one stable text object without knowing unrelated screens.
