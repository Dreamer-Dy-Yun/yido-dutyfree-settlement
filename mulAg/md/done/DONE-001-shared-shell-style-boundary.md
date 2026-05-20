# DONE: shared shell and style boundary

## 수행 일시

2026-05-20 21:35:00

## 참조 plan

- `mulAg/md/plan/done/PLAN-20260520-frontend-boundary-commonization.md`

## 참조한 todo

- `mulAg/md/todo/TODO-001.md`

## 수행 내용

- Tenant dashboard pages now use `DashboardShell` instead of assembling `Sidebar`, `SessionHeader`, current-user loading, logout, and profile refresh directly.
- Shared layout and common UI CSS moved to `src/styles/`.
- System admin layout imports shared styles from `src/styles/`.
- Tenant/admin page CSS no longer imports admin-owned common CSS.
- Folder responsibility docs added for `src/components/`, `src/hooks/`, and `src/styles/`.

## 변경 파일

- `README.md`
- `src/admin/components/SystemAdminLayout.jsx`
- `src/admin/pages/LlmApiKeyCreatePage.css`
- `src/admin/pages/PromptCreatePage.css`
- `src/admin/pages/PromptDetailPage.css`
- `src/admin/pages/ServiceAccountDetailPage.css`
- `src/admin/pages/ServiceAccountListPage.css`
- `src/admin/pages/SystemAdminDashboard.css`
- `src/admin/pages/TenantDetailPage.css`
- `src/admin/pages/TenantListPage.css`
- `src/pages/DataMappingPage.jsx`
- `src/pages/DataMappingPage.css`
- `src/pages/FeePage.jsx`
- `src/pages/TenantManagementPage.jsx`
- `src/pages/WorkspacePage.jsx`
- `src/pages/WorkspacePage.css`
- `mulAg/md/todo/TODO-001.md`

## 생성 파일

- `src/components/DashboardShell.jsx`
- `src/components/README.md`
- `src/hooks/useCurrentUser.js`
- `src/hooks/README.md`
- `src/styles/appLayout.css`
- `src/styles/commonUi.css`
- `src/styles/README.md`

## 미변경 파일

- `src/components/Sidebar.jsx`
- `src/components/SessionHeader.jsx`
- `src/api/auth/authApi.js`

## 검증 내용

- `rg` search found no stale `CommonUI.css` or `AppLayout.css` imports under source docs/code.
- `corepack pnpm run lint` passed.
- Source line-count check found no files over 300 lines.
- Sub-Agent QA found that moved CSS source files had been incorrectly listed as read-only; `TODO-001.md` was corrected to include them as editable files.

## 남은 이슈

- Data-mapping API still needs sub-boundary split under `TODO-002`.
- Upload UI duplication still needs cleanup under `TODO-003`.

## QA 확인 요청 사항

- Confirm that shared CSS ownership under `src/styles/` is acceptable for both tenant and system-admin flows.
