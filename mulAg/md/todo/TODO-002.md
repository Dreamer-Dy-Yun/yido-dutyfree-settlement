# TODO: data-mapping API sub-boundary split

## 참조 plan

- `mulAg/md/plan/done/PLAN-20260520-frontend-boundary-commonization.md`

## 목적

Data-mapping API calls should expose upload, review, image asset, and matching boundaries as separate modules.

## 작업 범위

- Split `dataMappingApi.js` into sub-domain API files.
- Keep `dataMappingApi.js` as a compatibility barrel.
- Update UI imports to the specific API sub-boundary.
- Update API documentation.

## 선행 조건

- `TODO-001` completed, because `DataMappingPage.jsx` may also change here.

## 수정 가능 파일

- `src/api/data-mapping/dataMappingApi.js`
- `src/api/README.md`
- `src/api/data-mapping/README.md`
- `src/pages/DataMappingPage.jsx`
- `src/data-mapping/EdiUploadPanel.jsx`
- `src/data-mapping/ImageZipUploadPanel.jsx`
- `src/data-mapping/ImageReviewPanel.jsx`
- `src/data-mapping/ImageVerifyModal.jsx`
- `src/data-mapping/ImageMappingPanel.jsx`
- `src/data-mapping/useImageViewerResources.js`
- `src/data-mapping/image-verify/useImageVerifyDetailState.js`
- `src/data-mapping/README.md`
- `src/data-mapping/image-verify/README.md`

## 생성 가능 파일

- `src/api/data-mapping/uploadApi.js`
- `src/api/data-mapping/reviewApi.js`
- `src/api/data-mapping/imageAssetApi.js`
- `src/api/data-mapping/matchingApi.js`
- `mulAg/md/review/REVIEW-002.md`

## 읽기 전용 파일

- `src/api/client/apiClient.js`
- `src/api/data-mapping/ediUnifiedApi.js`
- `mulAg/md/todo/TODO-001.md`

## 수정 금지 파일

- Backend files
- `node_modules/`
- `dist/`

## 입력

- Existing data-mapping API functions and UI imports.

## 출력

- Sub-domain data-mapping API files.
- Specific UI imports for each sub-contract.

## 작업 단계

- [ ] Create sub-domain API modules.
- [ ] Convert `dataMappingApi.js` to a re-export barrel.
- [ ] Update UI imports.
- [ ] Update docs.
- [ ] Search for stale imports.

## 완료 기준

- No UI component imports data-mapping functions from an over-broad file unless compatibility is required.
- No endpoint behavior changes.
- Lint/test/build remain passable.

## 주의사항

- Keep function names stable.
- Do not invent backend fields.
