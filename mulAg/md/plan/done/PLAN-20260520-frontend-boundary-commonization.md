# PLAN: frontend boundary commonization

## 작성 일시

2026-05-20

## 요구사항

- 프론트엔드 구조를 파악하고 문제점과 수정할 부분을 정리한다.
- 공통화와 경계 분리를 최우선으로 진행한다.
- CSS, 기능, API 요청 중 중첩된 부분을 공통화한다.
- API 요청 중복은 정리하고 책임 경계에 따라 폴더와 파일을 나눈다.

## 현재 문제점

1. Tenant dashboard pages repeat the same layout assembly.
   - `DataMappingPage`, `FeePage`, `WorkspacePage`, `TenantManagementPage` each load current user, render `Sidebar`, render `SessionHeader`, and build the same app shell.
   - The repeated shell makes profile refresh/logout behavior drift-prone.

2. Shared CSS is stored under admin folders.
   - Tenant pages import `src/admin/pages/CommonUI.css` and `src/admin/components/AppLayout.css`.
   - This makes common UI ownership look admin-specific even though tenant pages depend on it.

3. Data-mapping API is still too broad.
   - `src/api/data-mapping/dataMappingApi.js` mixes upload, OCR review, image asset, and matching APIs.
   - UI components cannot express which data-mapping sub-contract they depend on.

4. Upload panels duplicate behavior.
   - `EdiUploadPanel` and `ImageZipUploadPanel` repeat file state, drag/drop, upload state, and success/error rendering.
   - Only accepted file type, copy, extra controls, and upload function differ.

5. Error normalization is inconsistent.
   - `src/utils/normalizeApiError.js` exists, but several panels still read `err.response?.data?.detail` directly.
   - This hides the intended utility boundary.

## 수정 방향

1. Create a shared dashboard shell and current-user hook for tenant dashboard pages.
2. Move shared layout/common UI CSS into `src/styles/`.
3. Split data-mapping API files by sub-domain while keeping a compatibility barrel.
4. Extract a reusable data-mapping upload panel for EDI and image ZIP upload flows.
5. Update related README files with the new boundaries.

## 실행 순서

1. `TODO-001`: shared shell/style boundary.
2. `TODO-002`: data-mapping API sub-boundary split.
3. `TODO-003`: data-mapping upload UI commonization.

## 검증 기준

- `git diff --check`
- `corepack pnpm run lint`
- `corepack pnpm run test:run`
- `VITE_API_BASE_URL=/api corepack pnpm run build`
- Source files remain below the 300-line target unless explicitly justified.

## 완료 상태

- `TODO-001` through `TODO-004` were implemented.
- Sub-Agent QA findings were reflected before final validation.
- Final validation passed with diff check, lint, tests, and production build.
