# Backend Module Boundaries

This document records backend responsibility boundaries for maintenance and LLM-assisted work. When API contracts, DB schemas, folder responsibilities, or module boundaries change, update this file and the relevant folder README in the same change.

## Hardening Rules

A hardened module is a reusable contract unit. Its public methods, parameters, return values, side effects, and allowed change surface must be clear enough that callers can use the documented contract without reading internals.

Do not modify a hardened module unless the user explicitly allows it for that task.

## Hardened Or Protected Modules

| Module | Status | Protected contract |
| --- | --- | --- |
| `DATABASE/dbms/postgre/pg_manager.py` | Hardened protection target | Engine/session setup, schema search path handling, table create/drop, query execution, DataFrame conversion, upsert/update conflict-key behavior. |
| `DATABASE/dbms/db_manager.py` | Contract interface | Abstract DB manager methods used by routers, repositories, processors, and tests. |
| `DATABASE/repositories/base.py` | Contract interface | Basic repository dependency on `DBManager`; concrete repositories should preserve this boundary. |
| `WEB_SERVER/auth/jwt.py` | Small auth contract | JWT encode/decode behavior and exception shape. |
| `WEB_SERVER/auth/password.py` | Small auth contract | Password hashing and verification utilities. |
| `PROCESSOR_DATA/edi_processor.py` | Processor contract | Parser lifecycle: set input, parse vendor columns, convert to unified output. |
| `PROCESSOR_MATCHING/matcher.py` | Matcher contract | Lock/fetch, match, fallback, flush, and JSON result shape for passport-receipt matching. |
| `LLM/llm.py` and `LLM/dto.py` | LLM contract | Request/response DTOs, streaming/non-streaming method expectations, close lifecycle. |

## Split Candidates

| Module | Current problem | Preferred split direction |
| --- | --- | --- |
| `WEB_SERVER/routers/router_tenant.py` | Multiple API domains and direct DB/service orchestration in one file. | Split by tenant users, EDI upload/unified/export, image OCR/review, matching, receipt/passport verification, usage/info, internal worker APIs. |
| `WEB_SERVER/routers/router_system_admin.py` | Provider admin APIs, schemas, and DB operations are mixed. | Split tenants, service accounts, LLM API keys, and prompts into separate routers or service modules. |
| `WEB_SERVER/services/service_email.py` | Transport, templates, account lookup, and email cases are mixed in one large service. | Split SMTP account resolution, message construction, transport adapter, and individual email templates. |
| `DATABASE/models/tenant_model.py` | Many tenant schema tables live in one file. | Split only with stable re-export from `DATABASE.models` and migration/import compatibility checks. |

## API Layer Boundary

Routers may:

- Validate HTTP inputs with FastAPI/Pydantic.
- Resolve auth dependencies.
- Select the tenant/public schema for a request.
- Call services, repositories, processors, and DB manager methods.
- Convert domain results into API responses.

Routers should not:

- Hide backend contract mismatches by inventing fake success states.
- Mix unrelated API domains during new work.
- Perform large business workflows inline when a service boundary already exists.

## Service Boundary

Services own workflows that cross DB, Redis, email, filesystem, processors, or external APIs. Services should keep failure states visible and should not make mock or temporary behavior look like durable persistence.

## Database Boundary

The DB layer owns SQLAlchemy models, schema creation, repository access, and PostgreSQL-specific behavior. DB constraints remain the source of truth for FK, unique, and nullability rules; do not replace them with router-only checks.

## Worker Boundary

Workers consume Redis jobs, call internal API endpoints, and report job status. The internal API still owns tenant schema validation and DB mutation.

## Known Open Issues

- `WEB_SERVER/routers/router_registration.py` is present but not registered by the active FastAPI app.
- Several source files contain mojibake in comments or OpenAPI descriptions. Fixing this should be a dedicated encoding/documentation pass.
- The parent git worktree currently shows broad file moves/deletions outside `backend/`. Backend-only tasks must avoid touching frontend or unrelated parent paths.
