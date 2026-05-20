# DONE: data-mapping API sub-boundary split

## 수행 일시

2026-05-20 21:45:00

## 참조 plan

- `mulAg/md/plan/done/PLAN-20260520-frontend-boundary-commonization.md`

## 참조한 todo

- `mulAg/md/todo/TODO-002.md`

## 수행 내용

- Split data-mapping APIs into upload, review, image asset, and matching sub-boundaries.
- Kept `dataMappingApi.js` as a compatibility barrel.
- Updated UI imports to use the most specific data-mapping API file.
- Updated API and feature README files to document the new boundary.

## 변경 파일

- `src/api/README.md`
- `src/api/data-mapping/README.md`
- `src/api/data-mapping/dataMappingApi.js`
- `src/data-mapping/EdiUploadPanel.jsx`
- `src/data-mapping/ImageZipUploadPanel.jsx`
- `src/data-mapping/ImageReviewPanel.jsx`
- `src/data-mapping/ImageVerifyModal.jsx`
- `src/data-mapping/ImageMappingPanel.jsx`
- `src/data-mapping/useImageViewerResources.js`
- `src/data-mapping/image-verify/useImageVerifyDetailState.js`
- `src/data-mapping/README.md`
- `src/data-mapping/image-verify/README.md`
- `src/pages/DataMappingPage.jsx`
- `mulAg/md/todo/TODO-002.md`

## 생성 파일

- `src/api/data-mapping/uploadApi.js`
- `src/api/data-mapping/reviewApi.js`
- `src/api/data-mapping/imageAssetApi.js`
- `src/api/data-mapping/matchingApi.js`

## 미변경 파일

- `src/api/client/apiClient.js`
- `src/api/data-mapping/ediUnifiedApi.js`

## 검증 내용

- `rg` search found no UI imports from `dataMappingApi.js`.
- `corepack pnpm run lint` passed.
- Source line-count check found no files over 300 lines.
- Sub-Agent QA found `src/api/README.md` missing from the todo access list; `TODO-002.md` was corrected.

## 남은 이슈

- EDI and image ZIP upload panels still duplicate UI behavior and should be handled by `TODO-003`.

## QA 확인 요청 사항

- Confirm that keeping `dataMappingApi.js` as a compatibility barrel is acceptable while new imports use specific sub-boundary files.
