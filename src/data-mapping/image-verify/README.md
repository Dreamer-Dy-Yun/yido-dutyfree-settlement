# Image Verify Components

Image verification modal subcomponents live here.

| File | Responsibility |
| --- | --- |
| `ConfirmDialog.jsx` | Generic confirm dialog used by save, overwrite, and delete flows. |
| `ImageVerifyFields.jsx` | Receipt/passport edit target toggle and form fields. |
| `ImageVerifyHeader.jsx` | Modal title and close button rendering. |
| `ImageVerifyDataCards.jsx` | Verified/unverified receipt and passport quick-select cards. |
| `ImageVerifyFooter.jsx` | Modal navigation and save/delete/cancel actions. |
| `ImageVerifyDialogs.jsx` | Save, overwrite, and delete confirmation dialog composition. |
| `useImageVerifyDetailState.js` | Detail loading, edit target, form, coordinate, and transient UI state setup. |
| `useImageVerifyShortcuts.js` | Keyboard shortcut handling for close, confirm, and previous/next navigation. |
| `imageVerifyRequestBuilders.js` | Pure helpers that resolve verify targets and build API request payloads. |
| `imageVerifyRequestBuilders.test.js` | Payload builder tests for receipt/passport verification requests. |

## Boundary

- `ImageVerifyModal.jsx` owns save/delete orchestration and calls backend only through `src/api/data-mapping/dataMappingApi.js`.
- Components in this folder render modal UI only and receive data/actions through props.
- Keyboard behavior stays in `useImageVerifyShortcuts.js`; UI text comes from `src/locales/KO.js`.
- Request payload changes must update `imageVerifyRequestBuilders.test.js` with the expected API contract.
