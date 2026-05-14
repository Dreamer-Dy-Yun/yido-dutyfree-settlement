# WEB_SERVER/routers

This folder contains FastAPI route modules and router-local helpers.

## Active Routers

| Path | Prefix | Responsibility |
| --- | --- | --- |
| `router_auth.py` | `/api/auth` | Tenant/system-admin login, refresh/logout, current profile, password update, token-expiry settings. |
| `router_company.py` | `/api/company` | Company search and company registration request flow. |
| `router_tenant.py` | `/api/tenant` | Tenant user management, EDI APIs, image upload/OCR/review, matching, receipt/passport verification, usage, tenant public info, internal worker endpoints. |
| `router_system_admin.py` | `/api/system-admin` | Provider admin dashboard, tenant approval/lifecycle, service accounts, masked LLM API keys, prompts. |

## Inactive Or Unconfirmed Routers

| Path | Current status |
| --- | --- |
| `router_registration.py` | Defines `/api/registration` endpoints but is not included by `WEB_SERVER/app.py`. Confirm before relying on it. |

## Supporting Files

| Path | Responsibility |
| --- | --- |
| `tenant_schemas.py` | Pydantic request/response schemas used by tenant routes. |
| `tenant_helpers.py` | Shared tenant-route helpers for schema lookup, verified row merge/upsert/archive support, email/receipt normalization, and image payload shaping. |
| `responses.py` | JSON gzip response helper. |
| `settings.py` | FastAPI dependency providers for `DBManager`, `UserRepository`, and `TenantRepository`. |
| `TEMPLATE/DashBoard_PPM.xltx` | Excel template used by router/export behavior. |
| `__init__.py` | Router package marker. |

## Split Plan For `router_tenant.py`

`router_tenant.py` is a split candidate. Preserve behavior while extracting in small API-domain steps:

| Target domain | Candidate endpoints |
| --- | --- |
| Tenant users | `/users`, `/users/{user_id}`, activation, reset-password, token usage. |
| EDI unified | `/data-mapping/edi-upload`, `/data-mapping/edi-unified/*`. |
| Image OCR/review | `/data-mapping/image-upload`, OCR progress, image file/detail APIs. |
| Matching | `/data-mapping/match-*`, `/data-mapping/matches*`, `/internal/match/run`. |
| Verification | Receipt/passport verify, delete, and bulk-verify endpoints. |
| Tenant info/usage | `/usage`, `/info`. |

## Split Plan For `router_system_admin.py`

Separate by provider-admin domain:

- Tenant lifecycle and approval.
- Service accounts.
- LLM API keys.
- Prompts.
- Dashboard stats.

## Boundary Notes

- New routes should define clear request/response schema contracts.
- Internal worker endpoints must remain separate from user-facing endpoints.
- Do not add frontend-only fake fields. If data is missing, expose an empty/error state or update the API contract.
- `/api/tenant/info` reads and updates the current user's public tenant record by `schema_name`; it must not return placeholder success responses.
- LLM API key responses must return masked secrets only. Use the model masking contract instead of returning raw `api_key` values.
