# DONE: data-mapping upload UI commonization

## 수행 일시

2026-05-20 21:53:00

## 참조 plan

- `mulAg/md/plan/done/PLAN-20260520-frontend-boundary-commonization.md`

## 참조한 todo

- `mulAg/md/todo/TODO-003.md`

## 수행 내용

- Created a shared data-mapping upload panel for drag/drop, file selection, upload state, and result rendering.
- Refactored EDI upload and image ZIP upload panels into feature-specific wrappers.
- Moved upload panel/dropzone styles into `src/data-mapping/upload/`.
- Switched upload error rendering to `normalizeApiError`.
- Documented the upload subfolder boundary.

## 변경 파일

- `src/data-mapping/EdiUploadPanel.jsx`
- `src/data-mapping/ImageZipUploadPanel.jsx`
- `src/data-mapping/README.md`
- `src/pages/DataMappingPage.css`
- `src/pages/DataMappingPage.jsx`
- `mulAg/md/todo/TODO-003.md`

## 생성 파일

- `src/data-mapping/upload/FileUploadPanel.jsx`
- `src/data-mapping/upload/FileUploadPanel.css`
- `src/data-mapping/upload/README.md`
- `src/data-mapping/DataMappingFeedback.css`

## 미변경 파일

- `src/api/data-mapping/uploadApi.js`
- `src/utils/normalizeApiError.js`

## 검증 내용

- `rg` confirmed old EDI-specific upload/dropzone classes are no longer referenced by JSX.
- `corepack pnpm run lint` passed.
- Source line-count check found no files over 300 lines.
- Sub-Agent QA found a style boundary leak from `FileUploadPanel.jsx` to `DataMappingPage.css`; shared feedback styles were moved to `DataMappingFeedback.css`.
- Sub-Agent QA found direct `err.response?.data?.detail` access in `DataMappingPage.jsx`; it now uses `normalizeApiError`.

## 남은 이슈

- Broader error normalization remains inconsistent in older admin/workspace pages and should be a later todo if desired.

## QA 확인 요청 사항

- Confirm that the reusable upload panel should remain feature-scoped under `src/data-mapping/upload/` rather than moving to global `src/components/`.
