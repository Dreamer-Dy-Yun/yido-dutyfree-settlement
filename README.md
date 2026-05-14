# YIDO Backend Worktree

This worktree is the backend and server-orchestration side of YIDO.

## DONE

- Backend runtime code was moved under `backend/`.
- nginx configuration was moved under `infra/nginx/`.
- Current project documentation was moved under `MD/`.
- Historical notes and TODO records are kept under `MD/HISTORY/`.
- Frontend source is no longer owned by this worktree.

## TODO

- Commit the backend-branch restructure after review.
- Keep `D:\DEV\YIDO\frontend` as the frontend branch worktree.
- Remove the empty `frontend/` directory after the Windows file handle is released.
- Re-run backend tests after Python environment selection is confirmed.
- Re-run Docker Compose after Docker Desktop is available.

## Folder Responsibilities

| Path | Responsibility |
| --- | --- |
| `backend/` | FastAPI backend, database layer, workers, processors, LLM/OCR integration, backend tests |
| `infra/nginx/` | nginx config used by Docker Compose |
| `MD/` | current project documentation and agent handoff notes |
| `MD/HISTORY/` | historical plans, completed progress notes, old TODO records |
| `docker-compose.yml` | local/server orchestration for backend, workers, PostgreSQL, Redis, pgAdmin, and nginx |

## Backend Commands

Run backend commands from `backend/`.

```powershell
cd backend
python -m pytest -q
```

## Docker Commands

Run Compose commands from this worktree root.

```powershell
docker compose config --quiet
docker compose up -d --build
```

For local frontend static serving, build the frontend in `D:\DEV\YIDO\frontend` first. The default `NGINX_FRONTEND_DIST` points to `./frontend/dist`.
