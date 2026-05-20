# TODO: shared shell and style boundary

## 참조 plan

- `mulAg/md/plan/done/PLAN-20260520-frontend-boundary-commonization.md`

## 목적

Tenant dashboard pages should not repeat current-user loading and app shell assembly, and shared CSS should not live under admin folders.

## 작업 범위

- Create shared current-user hook.
- Create shared dashboard shell component.
- Move common layout/style ownership from admin folders to `src/styles/`.
- Update tenant/admin imports and documentation.

## 선행 조건

- 없음

## 수정 가능 파일

- `src/pages/DataMappingPage.jsx`
- `src/pages/FeePage.jsx`
- `src/pages/WorkspacePage.jsx`
- `src/pages/TenantManagementPage.jsx`
- `src/pages/DataMappingPage.css`
- `src/pages/WorkspacePage.css`
- `src/admin/components/SystemAdminLayout.jsx`
- `src/admin/components/AppLayout.css`
- `src/admin/pages/CommonUI.css`
- `src/admin/pages/*.css`
- `README.md`

## 생성 가능 파일

- `src/components/DashboardShell.jsx`
- `src/hooks/useCurrentUser.js`
- `src/styles/appLayout.css`
- `src/styles/commonUi.css`
- `src/styles/README.md`
- `src/components/README.md`
- `src/hooks/README.md`
- `mulAg/md/review/REVIEW-001.md`

## 읽기 전용 파일

- `src/components/Sidebar.jsx`
- `src/components/SessionHeader.jsx`
- `mulAg/common-rules.md`
- `mulAg/orchestrator.md`

## 수정 금지 파일

- Backend files
- `node_modules/`
- `dist/`

## 입력

- Existing tenant dashboard page layout.
- Existing admin layout and common UI styles.

## 출력

- Shared dashboard shell and style boundary.
- Tenant/admin pages depending on `src/styles/` rather than admin-owned CSS.

## 작업 단계

- [ ] Create shared hook and shell.
- [ ] Move common CSS content into `src/styles/`.
- [ ] Update page/layout imports.
- [ ] Update documentation.
- [ ] Verify no stale imports remain.

## 완료 기준

- Tenant dashboard pages use the shared shell.
- Shared CSS imports no longer point from tenant pages to admin folders.
- Lint/test/build remain passable.

## 주의사항

- Do not change route behavior.
- Preserve existing UI rhythm and class names where possible.
