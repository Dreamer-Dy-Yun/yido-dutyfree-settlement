# Backend MD Guide

Updated: 2026-05-14

This folder contains current documentation for the backend worktree and server orchestration.

## DONE

- Backend runtime code is under `backend/`.
- nginx deployment config is under `infra/nginx/`.
- Current backend/server documentation is under `MD/`.
- Historical implementation notes, old plans, and completed TODO files are under `MD/HISTORY/`.
- Frontend-specific documentation was moved out of the current backend document set.

## TODO

- Review and commit the backend branch restructure.
- Re-run backend tests after the Python environment is selected.
- Re-run Docker Compose after Docker Desktop is available.
- Remove the empty locked `frontend/` folder once the Windows file handle is released.
- Keep frontend deployment workflow implementation in `D:\DEV\YIDO\frontend`.

## Current Documents

| File | Responsibility |
| --- | --- |
| `ARCHITECTURE.md` | system architecture and backend/server ownership boundaries |
| `AUTHENTICATION_FLOW.md` | auth/session flow and API ownership notes |
| `CICD_AND_DEPLOYMENT.md` | backend/server CI, Docker, and deployment notes |
| `DB_TRANSACTION_RISK_CHECKLIST.md` | database transaction and integrity risk checklist |
| `MODULE_BOUNDARIES.md` | module ownership and refactor boundary notes |
| `PROJECT_SKELETON.md` | compact backend/server implementation map |
| `PROJECT_STRUCTURE_CURRENT.md` | current backend worktree folder structure |
| `HISTORY/` | historical notes, completed progress logs, and old plans |
