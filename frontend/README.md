# Frontend Structure

The frontend is a React + Vite application for tenant users and system administrators.
It is now structured so this folder can become its own repository later.

## Commands

```bash
pnpm install
copy .env.example .env
pnpm run dev
pnpm run lint
pnpm run build
```

`VITE_API_BASE_URL` defaults to `http://localhost:10000` when not set.

## Folders

| Path | Responsibility |
| --- | --- |
| `src/App.jsx` | route registration for tenant and system admin flows |
| `src/api/` | backend API boundary, axios clients, token/session utilities, and domain API functions |
| `src/admin/` | system admin pages, layout, and common admin components |
| `src/pages/` | tenant/user pages such as login, workspace, data mapping, fee |
| `src/data-mapping/` | EDI upload panels, image review list/viewer, viewer geometry/hooks, verification modal, matching panel |
| `src/components/` | shared tenant UI shell components |
| `src/common/components/` | cross-flow shared components such as protected routes |
| `src/hooks/` | shared React hooks |
| `src/constants/` | tab and option constants |
| `src/locales/` | shared UI display text constants, currently Korean strings in `KO.js` |
| `src/utils/` | frontend utility functions |

## API Boundary

Components should not create axios or fetch calls directly. Add or adjust API calls in `src/api/` first, then consume those functions from pages, panels, hooks, or components.

## Refactor Notes

Frontend package management is standardized on pnpm. Keep `pnpm-lock.yaml` as the single dependency lockfile and do not add npm or yarn lockfiles.
`pnpm-workspace.yaml` records approved dependency build scripts; keep `esbuild` approved so Vite can install reproducibly under pnpm 11.

Known large workflow files have been split below the 300-line target by component/workflow boundary, including image verification, EDI unified check, tenant detail, and workspace management screens.
