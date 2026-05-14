# WEB_SERVER/services

This folder contains business workflow modules used by routers, background tasks, and worker-facing endpoints.

## Files

| Path | Responsibility |
| --- | --- |
| `auth_service.py` | Login, system-admin login, password verification/update, token refresh/logout, token-expiry preference workflows. |
| `company_service.py` | Company search and registration request workflow, including tenant lookup and notification email. |
| `registration_service.py` | User registration and email verification workflow. Currently paired with an unregistered router. |
| `service.py` | Small placeholder/example service. Confirm usage before extending. |
| `service_edi_unified_queue.py` | Redis enqueue/status helpers for EDI unified jobs. |
| `service_email.py` | Email service, SMTP transport/account handling, message composition, and email cases. Split candidate. |
| `service_image_ocr.py` | Resolves active LLM key/prompts and runs tenant image OCR through `ImageOcrRunner`. |
| `service_match_queue.py` | Redis enqueue helper for matching jobs. |
| `service_tenant_deletion.py` | Tenant filesystem deletion workflow for tenant lifecycle cleanup. |
| `service_verified_archive.py` | Archive helpers for deleted/changed verified receipt/passport rows. |
| `service_xxxxx.py` | Older or placeholder matching service. Confirm usage before extending. |
| `verification_token.py` | Email verification token generation, storage, lookup, and deletion. |
| `test_queue_services.py` | Unit coverage for Redis queue payload/status contracts using a fake Redis client. |
| `test_service_email.py` | Unit test for verification email composition/sending behavior. |
| `__init__.py` | Service package exports. |

## Boundary Notes

- Services may coordinate DB, Redis, email, filesystem, processors, and external APIs.
- Services should return explicit failure or raise clear exceptions rather than pretending temporary/mock actions persisted.
- When a service changes a user-visible API contract, update the relevant router README and schema docs.

## Split Candidate: `service_email.py`

Preferred future modules:

- SMTP account resolution from DB/service account config.
- Transport adapter.
- Message builders/templates.
- Public email workflow functions used by routers/services.
