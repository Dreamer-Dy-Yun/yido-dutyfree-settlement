# Frontend Path Flatten Impact

Updated: 2026-05-14

This document records the checks required after moving the Vite app from a nested `frontend/` source folder to the frontend worktree root.

## Current Rule

- `D:\DEV\YIDO\frontend` is the frontend repository root for day-to-day work.
- Source paths start at root-level folders such as `src/`, `public/`, `MD/`, and root files such as `package.json`, `index.html`, and `vite.config.js`.
- Do not add application code under a nested `frontend/` folder.
- `node_modules/` and `dist/` are generated folders and stay ignored.

## Impact Checked

| Area | Result |
| --- | --- |
| Source imports | No source import points to a nested `frontend/` path. |
| Vite root | `vite.config.js` uses the default root, which now correctly means this directory. |
| Build entry | `index.html` loads `/src/main.jsx`, which matches the root-level source tree. |
| API boundary | Components still call API functions through `src/api/`; no old `src/services/` or `common/apis/` boundary remains. |
| Git tracking | No tracked files remain under `frontend/`, backend runtime folders, DB folders, or nginx folders on the `frontend` branch. |
| CI/deploy docs | Workflow guidance watches root-level frontend paths and targets the `frontend` branch. |

## Regression Checks

Run these from the frontend repository root before committing path-sensitive changes:

```bash
git ls-files | rg '^(frontend/|WEB_SERVER/|DATABASE/|CUSTOMIZED/|LLM/|PROCESSOR_|nginx/|docs/|app/)'
rg -n 'src/services|src/admin/services|common/apis|cust_https' README.md src
corepack pnpm run lint
VITE_API_BASE_URL=/api corepack pnpm run build
corepack pnpm run test:run
```

The first two commands should return no matches.
