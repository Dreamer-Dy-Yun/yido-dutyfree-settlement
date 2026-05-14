# Frontend GitHub Actions Deploy Plan

Updated: 2026-05-14

This document is the handoff guide for the frontend agent that will create the GitHub Actions workflow for frontend build and deployment.

## DONE

- Frontend code has been moved to the frontend worktree root.
- The app is a React + Vite project.
- The package manager is `pnpm@11.1.1`.
- Build output is `dist`.
- Backend deployment is intended to run separately on the server through Docker Compose.
- nginx should serve frontend static files and proxy `/api/` to the backend container.

## TODO

- Add `.github/workflows/frontend-deploy.yml`.
- Configure GitHub variables and secrets without account-specific hardcoding.
- Build with `VITE_API_BASE_URL=/api` for production.
- Upload `dist` to the server nginx static path.
- Prefer release-directory deployment with an atomic `dist` symlink switch.
- Verify `/` returns `200` after deployment.
- Verify `/api/auth/me` returns `401` without login, proving nginx reaches the backend.
- Keep this workflow at the frontend repository root. If this branch later becomes a standalone repository, switch the trigger branch from `frontend` to the repository default branch.

## Runtime Model

```text
browser
  -> nginx:80
      -> /         static frontend files
      -> /api/*    backend Docker service
```

GitHub Actions should build and deploy static frontend files only. It should not manage backend containers by default.

## Required GitHub Variables

| Name | Example | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `/api` | frontend API base used at build time |
| `DEPLOY_PATH` | `/srv/yido/frontend/dist` | server directory or symlink mounted by nginx |
| `DEPLOY_KEEP_RELEASES` | `3` | optional number of releases to retain |

## Required GitHub Secrets

| Name | Purpose |
| --- | --- |
| `SSH_HOST` | deployment server hostname or IP |
| `SSH_PORT` | SSH port, usually `22` |
| `SSH_USER` | dedicated server deploy user |
| `SSH_PRIVATE_KEY` | private key authorized for the deploy user |

Do not hardcode a personal GitHub username, repository owner, personal token, or account-specific registry path.

## Build Commands

Run from the frontend repository root:

```bash
corepack enable
corepack prepare pnpm@11.1.1 --activate
pnpm install --frozen-lockfile
pnpm run lint
VITE_API_BASE_URL=/api pnpm run build
```

## Draft Workflow Shape

```yaml
name: Frontend Deploy

on:
  workflow_dispatch:
  push:
    branches:
      - frontend
    paths:
      - "src/**"
      - "public/**"
      - "index.html"
      - "package.json"
      - "pnpm-lock.yaml"
      - "vite.config.js"
      - ".github/workflows/frontend-deploy.yml"

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "24"
          cache: "pnpm"
          cache-dependency-path: pnpm-lock.yaml

      - name: Enable pnpm
        run: |
          corepack enable
          corepack prepare pnpm@11.1.1 --activate

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Lint
        run: pnpm run lint

      - name: Build
        run: pnpm run build
        env:
          VITE_API_BASE_URL: ${{ vars.VITE_API_BASE_URL || '/api' }}

      - name: Deploy static files
        uses: easingthemes/ssh-deploy@v5.1.0
        with:
          SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
          REMOTE_HOST: ${{ secrets.SSH_HOST }}
          REMOTE_PORT: ${{ secrets.SSH_PORT || '22' }}
          REMOTE_USER: ${{ secrets.SSH_USER }}
          SOURCE: dist/
          TARGET: ${{ vars.DEPLOY_PATH }}
          ARGS: "-rlgoDzvc --delete"
```

The draft direct deploy is acceptable for the first implementation. For production, prefer uploading to a timestamped release directory and switching a symlink after upload succeeds.

`DEPLOY_PATH` is a server runtime path, not a source checkout path. It can keep `/srv/yido/frontend/dist` even though the source repository no longer has a nested `frontend/` directory.

## Server Target

Recommended server shape:

```text
/srv/yido/
  frontend/
    releases/
    dist -> releases/current-release
  app/
    docker-compose.yml
    .env
```

The backend/infra compose `.env` should point nginx to:

```dotenv
NGINX_FRONTEND_DIST=/srv/yido/frontend/dist
```

## Verification

Expected after deployment:

| URL | Expected |
| --- | --- |
| `/` | `200` |
| `/assets/...` | `200` |
| `/api/auth/me` | `401` without login |
