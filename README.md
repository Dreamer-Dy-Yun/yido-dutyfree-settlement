# YIDO Backend

This repository root is the backend-only working area for the YIDO service. It contains the FastAPI API server, SQLAlchemy/PostgreSQL data layer, Redis-backed workers, EDI processors, matching logic, OCR/LLM integration, Docker Compose runtime, nginx infrastructure, and backend-oriented project documentation.

Run backend commands from this folder unless a command explicitly says otherwise.

## Path Contract

This folder is the backend repository root, Python runtime root, Git root, Docker Compose root, and documentation root for backend work.

The frontend is a separate sibling repository at `D:\DEV\YIDO\frontend`. Backend Compose serves frontend static files from `../frontend/dist` by default through `NGINX_FRONTEND_DIST`.

Current boundary documents live under `MD/`. Agent workflow documents live under `mulAg/`.

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

The current local checkout may also have a parent virtual environment used by existing tests:

```bash
..\venv\Scripts\python.exe -m pytest -q
```

`run.ps1` changes to this folder before starting `main.py`. It uses `.venv` when present, then falls back to the parent `..\venv`.

## Runtime Entry Points

| Path | Responsibility |
| --- | --- |
| `main.py` | Loads `.env`, runs `DATABASE.setup_db.setup_db`, starts the FastAPI server, and disposes the DB pool on shutdown. |
| `WEB_SERVER/app.py` | Creates the active FastAPI app, configures CORS/lifespan state, and registers active routers. |
| `WEB_SERVER/main_web.py` | Starts `WEB_SERVER.app:app` through uvicorn. Used by `Dockerfile`. |
| `PROCESSOR_MATCHING/run_match_worker.py` | Consumes Redis match jobs and calls the internal tenant match API. |
| `PROCESSOR_DATA/run_edi_unified_worker.py` | Consumes Redis EDI unified jobs and calls the internal tenant EDI API. |
| `docker-compose.yml` | Runs PostgreSQL, Redis, pgAdmin, backend API, nginx, and worker services from this backend root. |

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
| `WEB_SERVER/` | HTTP API layer, auth dependencies, routers, and service orchestration. |
| `DATABASE/` | SQLAlchemy models, PostgreSQL manager, repository layer, DB setup, and DB-oriented tests. |
| `PROCESSOR_DATA/` | EDI file parsing, normalization, EDI unified synchronization/export, and EDI worker. |
| `PROCESSOR_MATCHING/` | Receipt-passport matching contracts, concrete matchers, and Redis worker. |
| `PROCESSOR_LLM_RESULT/` | Image OCR runner and LLM OCR result parser. |
| `PROCESSOR_IMAGE/` | Image helper and POC code. |
| `LLM/` | LLM abstraction, DTOs, exceptions, ChatGPT implementation, and prompt files. |
| `CUSTOMIZED/` | Shared utilities for logging, hashing, parsing, retry, Excel/ZIP/web helpers. |
| `POC/` | Local experiments and examples; not part of the active runtime contract. |
| `app/` | Legacy or alternate FastAPI scaffold; current service flow uses `WEB_SERVER/`. |
| `infra/nginx/` | nginx config templates, Compose default config, and optional deployment helper. |
| `MD/` | Current backend structure, module boundary, and maintenance documentation. |
| `mulAg/` | Multi-agent plan/todo/review/done workflow documents. |

Each major backend folder has its own `README.md` with file-level responsibility notes.

## Boundary Documents

- `MD/MODULE_BOUNDARIES.md`: hardening status, protected modules, and refactor candidates.
- `WEB_SERVER/README.md`: API server boundary and active/inactive router status.
- `DATABASE/README.md`: DB layer boundary and ownership rules.
- `DATABASE/dbms/postgre/README.md`: `PGDBManager` hardening contract.
- `mulAg/role-reference-map.md`: multi-agent role document map.

## Current Refactor Pressure

These files exceed the default 300-line guideline and should be treated deliberately:

| Path | Current handling |
| --- | --- |
| `DATABASE/dbms/postgre/pg_manager.py` | Hardened protection target. Do not split or refactor without explicit user approval. |
| `DATABASE/models/tenant_model.py` | Schema contract file. Split only with a migration/import compatibility plan. |

Recent cleanup split the tenant router, system-admin router, and email service into smaller boundary files. Keep those aggregators thin and put new logic into the responsible sub-router or service module.

## Tests

The default test run is unit-level only. DB/Redis integration tests are not collected by default, so the default result should not contain skipped tests.

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

The backend image is defined by `Dockerfile` and is used by the local Compose stack for the API service and workers.

```bash
docker build -t yido-dutyfree-backend:local .
```

Run the full stack from this backend repository root:

```bash
docker compose config --quiet
docker compose up -d --build
```

For local frontend static serving, build the frontend in `D:\DEV\YIDO\frontend` first. The default `NGINX_FRONTEND_DIST` points to `../frontend/dist`.