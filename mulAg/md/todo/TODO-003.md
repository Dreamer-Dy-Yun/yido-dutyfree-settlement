# TODO: data-mapping upload UI commonization

## 참조 plan

- `mulAg/md/plan/done/PLAN-20260520-frontend-boundary-commonization.md`

## 목적

EDI upload and image ZIP upload should share drag/drop, file state, upload state, and result rendering.

## 작업 범위

- Create a reusable upload panel inside the data-mapping feature boundary.
- Refactor EDI and image ZIP upload panels to use it.
- Use shared error normalization.
- Document the upload subfolder boundary.

## 선행 조건

- `TODO-002` completed, because upload API imports should come from `uploadApi.js`.

## 수정 가능 파일

- `src/data-mapping/EdiUploadPanel.jsx`
- `src/data-mapping/ImageZipUploadPanel.jsx`
- `src/data-mapping/README.md`
- `src/pages/DataMappingPage.css`
- `src/pages/DataMappingPage.jsx`

## 생성 가능 파일

- `src/data-mapping/upload/FileUploadPanel.jsx`
- `src/data-mapping/upload/FileUploadPanel.css`
- `src/data-mapping/upload/README.md`
- `src/data-mapping/DataMappingFeedback.css`
- `mulAg/md/review/REVIEW-003.md`

## 읽기 전용 파일

- `src/api/data-mapping/uploadApi.js`
- `src/utils/normalizeApiError.js`
- `mulAg/md/todo/TODO-002.md`

## 수정 금지 파일

- Backend files
- `node_modules/`
- `dist/`

## 입력

- Existing EDI/image ZIP upload UI behavior.

## 출력

- Shared upload panel with feature-specific wrappers.

## 작업 단계

- [ ] Create reusable upload panel.
- [ ] Refactor EDI upload wrapper.
- [ ] Refactor image ZIP upload wrapper.
- [ ] Update docs and stale import search.

## 완료 기준

- Upload wrappers keep their visible behavior.
- Drag/drop and upload state code is no longer duplicated.
- Lint/test/build remain passable.

## 주의사항

- Keep the data-mapping feature-specific upload component under `src/data-mapping/`, not global, unless another feature starts using it.
