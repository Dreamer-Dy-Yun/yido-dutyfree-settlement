# Data Mapping API

Tenant data-mapping API contracts live here.

| File | Responsibility |
| --- | --- |
| `dataMappingApi.js` | EDI/image upload, OCR review lists, receipt/passport verification, image blobs, and matching APIs. |
| `ediUnifiedApi.js` | EDI unified job, group listing/detail, and Excel export APIs. |

## Boundary

- Data-mapping UI components import backend functions from this folder.
- Pure UI geometry or request-building helpers stay in `src/data-mapping/`.
