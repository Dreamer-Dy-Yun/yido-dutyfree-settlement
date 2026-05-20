# WEB_SERVER/routers

This folder contains FastAPI route modules and router-local helpers.

## Active Routers

| Path | Prefix | Responsibility |
| --- | --- | --- |
| `router_auth.py` | `/api/auth` | Tenant/system-admin login, refresh/logout, current profile, password update, token-expiry settings. |
| `router_company.py` | `/api/company` | Company search and company registration request flow. |
| `router_registration.py` | `/api/registration` | User registration and email verification endpoints registered by `WEB_SERVER/app.py`. |
| `router_tenant.py` | `/api/tenant` | Aggregator for tenant-domain sub-routers. |
| `router_tenant_users.py` | inherited from `router_tenant.py` | Tenant user management, usage, token usage, and tenant public info endpoints. |
| `router_tenant_edi.py` | inherited from `router_tenant.py` | Aggregator for EDI job/export sub-routers. |
| `router_tenant_edi_jobs.py` | inherited from `router_tenant.py` | EDI upload, unified job enqueue/status, and internal EDI run endpoints. |
| `router_tenant_edi_exports.py` | inherited from `router_tenant.py` | EDI unified Excel export, group list, and group detail endpoints. |
| `router_tenant_image.py` | inherited from `router_tenant.py` | Image ZIP upload, OCR progress, image file response, and image detail endpoints. |
| `router_tenant_matching.py` | inherited from `router_tenant.py` | Aggregator for matching and verification sub-routers. |
| `router_tenant_match_jobs.py` | inherited from `router_tenant.py` | Match request, internal match run, and match status endpoints. |
| `router_tenant_match_results.py` | inherited from `router_tenant.py` | Match list/detail and receipt/passport review list endpoints. |
| `router_tenant_verification.py` | inherited from `router_tenant.py` | Receipt/passport verify, delete, and bulk-verify endpoints. |
| `router_system_admin.py` | `/api/system-admin` | Aggregator for provider-admin sub-routers. |
| `router_system_admin_dashboard.py` | inherited from `router_system_admin.py` | Provider admin dashboard stats endpoint. |
| `router_system_admin_tenants.py` | inherited from `router_system_admin.py` | Tenant list/detail/pending/update/activate/deactivate endpoints. |
| `router_system_admin_tenant_lifecycle.py` | inherited from `router_system_admin.py` | Tenant approve/reject/delete lifecycle endpoints. |
| `router_system_admin_service_accounts.py` | inherited from `router_system_admin.py` | Service account list/detail/create/update/delete endpoints. |
| `router_system_admin_llm_api_keys.py` | inherited from `router_system_admin.py` | Masked LLM API key list/detail/create/update/delete endpoints. |
| `router_system_admin_prompts.py` | inherited from `router_system_admin.py` | Prompt list/detail/create/update/delete endpoints. |

## Supporting Files

| Path | Responsibility |
| --- | --- |
| `tenant_schemas.py` | Pydantic request/response schemas used by tenant routes. |
| `tenant_helpers.py` | Shared tenant-route helpers for schema lookup, verified row merge/upsert/archive support, email/receipt normalization, and image payload shaping. |
| `responses.py` | JSON gzip response helper. |
| `settings.py` | FastAPI dependency providers for `DBManager`, `UserRepository`, and `TenantRepository`. |
| `TEMPLATE/DashBoard_PPM.xltx` | Excel template used by router/export behavior. |
| `__init__.py` | Router package marker. |

## Current Split State For `router_tenant.py`

`router_tenant.py` is now an aggregator. Preserve this shape for new tenant routes:

| Target domain | Candidate endpoints |
| --- | --- |
| Tenant users | `/users`, `/users/{user_id}`, activation, reset-password, token usage. |
| EDI unified | `/data-mapping/edi-upload`, `/data-mapping/edi-unified/*`. |
| Image OCR/review | `/data-mapping/image-upload`, OCR progress, image file/detail APIs. |
| Matching | `/data-mapping/match-*`, `/data-mapping/matches*`, `/internal/match/run`. |
| Verification | Receipt/passport verify, delete, and bulk-verify endpoints. |
| Tenant info/usage | `/usage`, `/info`. |

## Current Split State For `router_system_admin.py`

`router_system_admin.py` is now an aggregator. Add new provider-admin routes by domain-specific sub-router:

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
