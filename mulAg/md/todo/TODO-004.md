# TODO: shared API error normalization adoption

## 참조 plan

- `mulAg/md/plan/done/PLAN-20260520-frontend-boundary-commonization.md`

## 목적

UI code should consistently use `normalizeApiError` instead of directly reading `err.response?.data?.detail`.

## 작업 범위

- Replace direct axios/FastAPI detail extraction in pages and shared components.
- Preserve special handling where code needs structured `detail` objects.
- Update review notes with remaining intentional exceptions if any.

## 선행 조건

- `TODO-003` implemented and reviewed.

## 수정 가능 파일

- `src/admin/pages/*.jsx`
- `src/components/ProfileModal.jsx`
- `src/data-mapping/EdiUnifiedCheckPanel.jsx`
- `src/pages/CompanyRegisterPage.jsx`
- `src/pages/LoginPage.jsx`
- `src/pages/SystemAdminLoginPage.jsx`
- `src/pages/WorkspacePage.jsx`
- `mulAg/md/review/REVIEW-003.md`

## 생성 가능 파일

- `mulAg/md/review/REVIEW-004.md`

## 읽기 전용 파일

- `src/utils/normalizeApiError.js`
- `mulAg/md/todo/TODO-003.md`

## 수정 금지 파일

- Backend files
- `node_modules/`
- `dist/`

## 입력

- Existing UI catch blocks and `normalizeApiError` utility.

## 출력

- UI catch blocks use the shared error normalization boundary unless structured detail handling is required.

## 작업 단계

- [ ] Import `normalizeApiError` where needed.
- [ ] Replace direct `err.response?.data?.detail || fallback` expressions.
- [ ] Keep structured detail handling intact.
- [ ] Search for remaining direct accesses and document intentional exceptions.

## 완료 기준

- Remaining direct `err.response?.data?.detail` accesses are intentional structured-detail cases only.
- Lint/test/build remain passable.

## 주의사항

- Do not rewrite business-specific duplicate company detection logic unless the API contract is clear.
