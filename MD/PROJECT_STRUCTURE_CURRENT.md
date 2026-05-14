# Current Backend Worktree Structure

Updated: 2026-05-14

## DONE

- `D:\DEV\YIDO` is the backend branch worktree.
- Backend source was moved into `backend/`.
- Server infrastructure config was moved into `infra/`.
- Current documentation was moved into `MD/`.
- Frontend branch work is now in `D:\DEV\YIDO\frontend`.

## TODO

- Delete the empty `frontend/` directory after its Windows file handle is released.
- Verify backend tests from `backend/`.
- Verify Docker Compose from the worktree root after Docker Desktop is available.
- Review the large backend files before any further split work.
- Commit only after checking that backend and frontend changes are no longer mixed.

## Root

| Path | Responsibility |
| --- | --- |
| `backend/` | backend application source, tests, Dockerfile, Python config |
| `infra/` | deployment infrastructure files such as nginx config |
| `MD/` | current backend/server documentation |
| `MD/HISTORY/` | historical notes and completed/old plans |
| `docker-compose.yml` | local/server orchestration for backend, workers, DB, Redis, pgAdmin, and nginx |
| `.env.example` | root Compose environment template |

## Backend

| Path | Responsibility |
| --- | --- |
| `backend/WEB_SERVER/` | FastAPI app, routers, auth, services |
| `backend/DATABASE/` | SQLAlchemy models, repositories, DB manager, DB setup and DB tests |
| `backend/PROCESSOR_DATA/` | EDI parsing, unified EDI processing, EDI worker |
| `backend/PROCESSOR_MATCHING/` | matching logic, matcher registry, matching worker |
| `backend/PROCESSOR_LLM_RESULT/` | OCR/LLM result parsing and image OCR runner |
| `backend/PROCESSOR_IMAGE/` | image processing helpers and experiments |
| `backend/LLM/` | LLM abstractions, DTOs, prompts, ChatGPT adapter |
| `backend/CUSTOMIZED/` | shared Python utilities |
| `backend/POC/` | local proof-of-concept scripts |
| `backend/app/` | legacy or alternate FastAPI scaffold |

## Infrastructure

| Path | Responsibility |
| --- | --- |
| `infra/nginx/compose.default.conf` | nginx config used by Docker Compose |
| `infra/nginx/nginx.conf.template` | nginx template used by deployment helper scripts |
| `infra/nginx/deploy_nginx.py` | legacy nginx deployment helper |

## Frontend Boundary

Frontend source is not owned by this worktree. Use:

```text
D:\DEV\YIDO\frontend
```

That worktree owns the React/Vite app root, frontend MD notes, and future GitHub Actions static deployment workflow.
