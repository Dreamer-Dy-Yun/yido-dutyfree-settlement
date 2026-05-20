# Data Mapping API

Tenant data-mapping API contracts live here.

| File | Responsibility |
| --- | --- |
| `uploadApi.js` | EDI spreadsheet and image ZIP upload APIs. |
| `reviewApi.js` | OCR progress, receipt/passport review lists, verification, deletion, and bulk verification APIs. |
| `imageAssetApi.js` | Image detail and image blob retrieval APIs. |
| `matchingApi.js` | Image matching status, matching trigger, matching list, and matching detail APIs. |
| `ediUnifiedApi.js` | EDI unified job, group listing/detail, and Excel export APIs. |
| `dataMappingApi.js` | Compatibility barrel that re-exports the sub-boundary modules; new UI imports should prefer the specific file. |

## Boundary

- Data-mapping UI components import backend functions from the most specific sub-boundary file.
- Pure UI geometry or request-building helpers stay in `src/data-mapping/`.
