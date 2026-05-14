# Frontend Structure

The frontend is a React + Vite application for tenant users and system administrators.
It is now structured so this folder can become its own repository later.

## Commands

```bash
npm install
copy .env.example .env
npm run dev
npm run lint
npm run build
```

`VITE_API_BASE_URL` defaults to `http://localhost:10000` when not set.

## Folders

| Path | Responsibility |
| --- | --- |
| `src/App.jsx` | route registration for tenant and system admin flows |
| `src/services/` | API access layer; UI components should call backend through this layer |
| `src/admin/` | system admin pages, layout, common admin components, admin API wrapper |
| `src/pages/` | tenant/user pages such as login, workspace, data mapping, fee |
| `src/data-mapping/` | EDI upload panels, image review list/viewer, viewer geometry/hooks, verification modal, matching panel |
| `src/components/` | shared tenant UI shell components |
| `src/common/components/` | cross-flow shared components such as protected routes |
| `src/hooks/` | shared React hooks |
| `src/constants/` | tab and option constants |
| `src/locales/` | shared UI display text constants, currently Korean strings in `KO.js` |
| `src/utils/` | frontend utility functions |

## API Boundary

Components should not create axios calls directly. Add or adjust API calls in `src/services/` first, then consume those functions from pages, panels, hooks, or components.

## Refactor Notes

Several frontend files still exceed the 300-line target. Split them by component/workflow boundary, not by arbitrary line count:

- `src/data-mapping/ImageVerifyModal.jsx`
- `src/admin/pages/TenantDetailPage.jsx`
- `src/data-mapping/EdiUnifiedCheckPanel.jsx`
- `src/pages/WorkspacePage.jsx`

`src/data-mapping/ImageViewer.jsx`, `src/data-mapping/ImageMappingPanel.jsx`, and `src/pages/DataMappingPage.jsx` are now below the 300-line target after extracting viewer geometry/hooks, matching status/table components, and upload panels.
