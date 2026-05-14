# Data Mapping

Tenant data-mapping screens and workflow-specific components live here.

| File | Responsibility |
| --- | --- |
| `EdiUploadPanel.jsx` | EDI spreadsheet upload UI and upload request trigger. |
| `ImageZipUploadPanel.jsx` | Image ZIP upload UI and upload request trigger. |
| `ImageReviewPanel.jsx` | Receipt/passport OCR review list workflow and bulk verification entry points. |
| `ImageReviewList.jsx` | Review list rendering, selection, and row actions. |
| `ImageVerifyModal.jsx` | Receipt/passport detail verification modal and save/delete flow. |
| `ImageViewer.jsx` | Image display, ROI overlay, pan/zoom, and editable ROI interaction. |
| `imageViewerGeometry.js` | Pure geometry helpers for image coordinates, ROI overlay, and viewport calculations. |
| `useImageViewerResources.js` | Browser resource hooks for viewer size, image blob URL, modifier key state, and wheel zoom. |
| `ImageMappingPanel.jsx` | Image matching status, matching trigger, result list, and detail modal orchestration. |
| `ImageMappingStatus.jsx` | Matching status summary and trigger button rendering. |
| `ImageMappingTable.jsx` | Matching result table, filters, empty/loading states, and pagination controls. |
| `MappingDetailModal.jsx` | Matched receipt/passport detail viewer and edit entry points. |
| `EdiUnifiedCheckPanel.jsx` | EDI unified data check, filtering, job status polling, and export workflow. |
| `edi-unified/` | EDI unified panel controls, result table, and tooltip subcomponents. |
| `image-verify/` | Image verification modal header, fields, dialogs, shortcuts, and request helpers. |

## Boundary

- Components in this folder call backend only through `src/services/tenant.js` or `src/services/ediUnified.js`.
- Shared Korean UI text is imported from `src/locales/KO.js`; avoid reintroducing duplicated Korean literals for the same workflow.
- Geometry calculations stay in `imageViewerGeometry.js`; React state and browser resource ownership stay in viewer hooks/components.
