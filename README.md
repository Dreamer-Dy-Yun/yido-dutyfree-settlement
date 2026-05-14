# Backend Structure

This folder is the backend-only working area for the YIDO service. It contains the FastAPI API server, SQLAlchemy/PostgreSQL data layer, Redis-backed workers, EDI processors, matching logic, OCR/LLM integration, and shared Python utilities.

Run backend commands from this folder unless a command explicitly says otherwise.

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

The current local checkout also has a parent virtual environment used by existing tests:

```bash
..\venv\Scripts\python.exe -m pytest -q
```

## Runtime Entry Points

| Path | Responsibility |
| --- | --- |
| `main.py` | Loads `.env`, runs `DATABASE.setup_db.setup_db`, starts the FastAPI server, and disposes the DB pool on shutdown. |
| `WEB_SERVER/app.py` | Creates the active FastAPI app, configures CORS/lifespan state, and registers active routers. |
| `WEB_SERVER/main_web.py` | Starts `WEB_SERVER.app:app` through uvicorn. Used by `Dockerfile`. |
| `PROCESSOR_MATCHING/run_match_worker.py` | Consumes Redis match jobs and calls the internal tenant match API. |
| `PROCESSOR_DATA/run_edi_unified_worker.py` | Consumes Redis EDI unified jobs and calls the internal tenant EDI API. |

## Active API Surface

The active app in `WEB_SERVER/app.py` registers these router prefixes:

| Prefix | Router | Boundary |
| --- | --- | --- |
| `/api/auth` | `WEB_SERVER/routers/router_auth.py` | Login, JWT refresh/logout, self profile, password and token-expiry settings. |
| `/api/company` | `WEB_SERVER/routers/router_company.py` | Public company search and company registration request flow. |
| `/api/tenant` | `WEB_SERVER/routers/router_tenant.py` | Tenant-scoped users, EDI, image OCR, matching, verification, usage, and tenant info APIs. |
| `/api/system-admin` | `WEB_SERVER/routers/router_system_admin.py` | Provider admin APIs for tenants, service accounts, LLM API keys, and prompts. |

`WEB_SERVER/routers/router_registration.py` exists but is not registered in `WEB_SERVER/app.py`. Treat it as inactive until the API contract is confirmed.

## Folder Index

| Path | Responsibility |
| --- | --- |
| `WEB_SERVER/` | HTTP API layer, auth dependencies, routers, service orchestration. |
| `DATABASE/` | SQLAlchemy models, PostgreSQL manager, repository layer, DB setup, DB-oriented tests. |
| `PROCESSOR_DATA/` | EDI file parsing, normalization, EDI unified synchronization/export, EDI worker. |
| `PROCESSOR_MATCHING/` | Receipt-passport matching contracts, concrete matchers, Redis worker. |
| `PROCESSOR_LLM_RESULT/` | Image OCR runner and LLM OCR result parser. |
| `PROCESSOR_IMAGE/` | Image helper and POC code. |
| `LLM/` | LLM abstraction, DTOs, exceptions, ChatGPT implementation, prompt files. |
| `CUSTOMIZED/` | Shared utilities for logging, hashing, parsing, retry, Excel/ZIP/web helpers. |
| `POC/` | Local experiments and examples; not part of the active runtime contract. |
| `app/` | Legacy or alternate FastAPI scaffold; current service flow uses `WEB_SERVER/`. |

Each major folder has its own `README.md` with file-level responsibility notes.

## Boundary Documents

- `MODULE_BOUNDARIES.md`: hardening status, protected modules, and refactor candidates.
- `WEB_SERVER/README.md`: API server boundary and active/inactive router status.
- `DATABASE/README.md`: DB layer boundary and ownership rules.
- `DATABASE/dbms/postgre/README.md`: `PGDBManager` hardening contract.

## Current Refactor Pressure

These files exceed the default 300-line guideline and should be treated deliberately:

| Path | Current handling |
| --- | --- |
| `WEB_SERVER/routers/router_tenant.py` | Split candidate. Separate by tenant users, EDI, image review, matching, verification, usage/info, and internal worker APIs. |
| `WEB_SERVER/routers/router_system_admin.py` | Split candidate. Separate tenants, service accounts, LLM API keys, and prompts. |
| `WEB_SERVER/services/service_email.py` | Split candidate. Separate SMTP account resolution, message composition, transport, and templates. |
| `DATABASE/dbms/postgre/pg_manager.py` | Hardened protection target. Do not split or refactor without explicit user approval. |
| `DATABASE/models/tenant_model.py` | Schema contract file. Split only with a migration/import compatibility plan. |

## Tests

The default test run is unit-level only. DB/Redis integration tests are not collected by default, so the default result should not contain skipped tests.
The default suite covers shared utilities, DB manager conflict-key selection, LLM DTO validation, EDI parser contracts, OCR result parsing, Redis queue payload contracts, and email composition.

```bash
..\venv\Scripts\python.exe -m pytest -q
```

Run integration tests only when a local PostgreSQL/Redis/schema environment is ready:

```bash
..\venv\Scripts\python.exe -m pytest -q --run-db-tests
```

The environment variable form is also supported:

```bash
$env:RUN_DB_TESTS = "1"
..\venv\Scripts\python.exe -m pytest -q
```

If this folder is used as a standalone repository with a local `.venv`, run:

```bash
.\.venv\Scripts\python.exe -m pytest -q
```

## Docker

The backend image is defined by `Dockerfile` and is used by the root compose stack for the API service and workers.

```bash
docker build -t yido-dutyfree-backend:local .
```
