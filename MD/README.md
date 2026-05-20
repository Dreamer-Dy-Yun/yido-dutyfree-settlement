# Frontend MD Guide

Updated: 2026-05-14

This folder contains current documentation for the frontend worktree.

## DONE

- The frontend branch now uses this worktree as the frontend-only project root.
- The Vite app was moved from `frontend/` to the worktree root.
- Backend runtime folders were removed from this frontend worktree.
- Generated frontend folders such as `node_modules` and `dist` were not moved.
- Path impact was checked after flattening: tracked source files no longer live under `frontend/`, and deploy/CI docs now target root-level frontend paths.
- API files are split by boundary under `src/api/{client,auth,tenant,data-mapping,admin}`.
- Browser `alert`/`confirm` calls are centralized behind `src/utils/userFeedback.js`.
- Dependencies were reinstalled with `pnpm install --frozen-lockfile`.
- `pnpm run lint` passed.
- `pnpm run test:run` now runs Vitest boundary tests.
- `VITE_API_BASE_URL=/api pnpm run build` passed.

## TODO

- Create the GitHub Actions workflow from `FRONTEND_GITHUB_ACTIONS_DEPLOY_PLAN.md`.
- After the backend worktree is cleaned, confirm the two branches no longer carry each other's runtime code.

## Current Documents

| File | Responsibility |
| --- | --- |
| `README.md` | frontend documentation index and worktree state |
| `FRONTEND_GITHUB_ACTIONS_DEPLOY_PLAN.md` | frontend GitHub Actions static build/deploy implementation guide |
| `PATH_FLATTEN_IMPACT.md` | impact checklist for the move from nested `frontend/` source paths to the repository root |
| `../mulAg/README.md` | multi-agent operation rules and plan/todo/review/done workflow index |
