# WEB_SERVER/services

This folder contains business workflow modules used by routers, background tasks, and worker-facing endpoints.

## Files

| Path | Responsibility |
| --- | --- |
| `auth_service.py` | Login, system-admin login, password verification/update, token refresh/logout, token-expiry preference workflows. |
| `company_service.py` | Company search and registration request workflow, including tenant lookup and notification email. |
| `registration_service.py` | User registration and email verification workflow used by the registered `/api/registration` router. |
| `service.py` | Small placeholder/example service. Confirm usage before extending. |
| `service_edi_unified_queue.py` | Redis enqueue/status helpers for EDI unified jobs. |
| `service_email.py` | Email service facade, SMTP transport, account handling, and compatibility API for `EmailService.set_xxx_email(...).send(...)`. |
| `email_message_builder.py` | Shared MIME multipart message builder for email templates. |
| `email_templates.py` | Compatibility re-export module for email template builders. |
| `email_user_templates.py` | User verification and welcome email template builders. |
| `email_user_account_templates.py` | User temporary password and deletion email template builders. |
| `email_company_templates.py` | Company registration, approval, rejection, and deletion email template builders. |
| `service_image_ocr.py` | Resolves active LLM key/prompts and runs tenant image OCR through `ImageOcrRunner`. |
| `service_match_queue.py` | Redis enqueue helper for matching jobs. |
| `service_tenant_deletion.py` | Tenant filesystem deletion workflow for tenant lifecycle cleanup. |
| `service_verified_archive.py` | Archive helpers for deleted/changed verified receipt/passport rows. |
| `service_xxxxx.py` | Older or placeholder matching service. Confirm usage before extending. |
| `verification_token.py` | Email verification token generation, storage, lookup, and deletion. |
| `test_queue_services.py` | Unit coverage for Redis queue payload/status contracts using a fake Redis client. |
| `test_service_email.py` | Unit test for verification email composition/sending behavior. |
| `test_backend_contract_hardening.py` | Contract coverage for hardened backend compatibility surfaces. |
| `__init__.py` | Service package exports. |

## Boundary Notes

- Services may coordinate DB, Redis, email, filesystem, processors, and external APIs.
- Services should return explicit failure or raise clear exceptions rather than pretending temporary/mock actions persisted.
- When a service changes a user-visible API contract, update the relevant router README and schema docs.

## Split State: `service_email.py`

Completed split:

- Message builders/templates are separated by user/company domain.
- `service_email.py` keeps the public `EmailService` facade, SMTP transport, and DB account resolver for compatibility.
- Existing chaining style `EmailService(...).set_xxx_email(...).send(...)` remains the supported contract.

Remaining future split candidates:

- SMTP account resolution from DB/service account config.
- Transport adapter.
- Public email workflow functions used by routers/services.
