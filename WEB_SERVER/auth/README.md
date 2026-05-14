# WEB_SERVER/auth

This folder owns authentication and session utilities for the active FastAPI app.

## Files

| Path | Responsibility |
| --- | --- |
| `config.py` | Auth-related environment settings, OAuth2 scheme, JWT secret/algorithm/expiration defaults. |
| `dependencies.py` | FastAPI dependencies for current tenant user, active user, system admin, and tenant admin checks. |
| `google_oauth.py` | Google OAuth flow helpers and Google token/user-info validation. |
| `jwt.py` | JWT access-token creation and token decoding. Small protected auth contract. |
| `password.py` | Password hashing and verification helpers. Small protected auth contract. |
| `redis_session.py` | Redis client factory and session manager for token validity, TTL extension, logout, and token-expiry preferences. |
| `__init__.py` | Auth package exports. |

## Boundary Notes

- Auth dependencies may read from Redis and the relevant tenant/public DB schema.
- Route handlers should depend on these functions instead of decoding JWTs directly.
- Session invalidation and TTL behavior belong in `redis_session.py`.
