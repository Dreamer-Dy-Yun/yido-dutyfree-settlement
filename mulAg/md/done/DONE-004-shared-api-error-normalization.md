# DONE: shared API error normalization adoption

## 수행 일시

2026-05-20 22:08:00

## 참조 plan

- `mulAg/md/plan/done/PLAN-20260520-frontend-boundary-commonization.md`

## 참조한 todo

- `mulAg/md/todo/TODO-004.md`

## 수행 내용

- Replaced direct `err.response?.data?.detail || fallback` handling across admin pages, login pages, workspace, profile modal, and EDI unified panel.
- Kept the structured `detail` read in `ImageVerifyModal.jsx` because it checks `force_merge_required`, not just a display string.
- Reused the existing `normalizeApiError` utility instead of adding a new error helper.

## 변경 파일

- `src/admin/pages/LlmApiKeyCreatePage.jsx`
- `src/admin/pages/LlmApiKeyListPage.jsx`
- `src/admin/pages/PromptCreatePage.jsx`
- `src/admin/pages/PromptDetailPage.jsx`
- `src/admin/pages/PromptListPage.jsx`
- `src/admin/pages/ServiceAccountDetailPage.jsx`
- `src/admin/pages/ServiceAccountListPage.jsx`
- `src/admin/pages/SystemAdminDashboard.jsx`
- `src/admin/pages/TenantDetailPage.jsx`
- `src/admin/pages/TenantListPage.jsx`
- `src/components/ProfileModal.jsx`
- `src/data-mapping/EdiUnifiedCheckPanel.jsx`
- `src/pages/CompanyRegisterPage.jsx`
- `src/pages/LoginPage.jsx`
- `src/pages/SystemAdminLoginPage.jsx`
- `src/pages/WorkspacePage.jsx`

## 생성 파일

- 없음

## 미변경 파일

- `src/utils/normalizeApiError.js`
- `src/data-mapping/ImageVerifyModal.jsx`

## 검증 내용

- `rg` search found only `src/utils/normalizeApiError.js` and the structured `force_merge_required` branch in `ImageVerifyModal.jsx` still read response detail directly.

## 남은 이슈

- None for this todo.

## QA 확인 요청 사항

- Confirm the `ImageVerifyModal.jsx` structured detail exception remains intentional.
