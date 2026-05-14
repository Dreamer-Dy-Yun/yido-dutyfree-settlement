# EDI Unified Components

EDI unified check subcomponents live here.

| File | Responsibility |
| --- | --- |
| `EdiUnifiedControls.jsx` | Date/source filters and job/export action buttons. |
| `EdiUnifiedGroupTable.jsx` | Unified group table, detail line table, badges, pagination, and note hover events. |
| `EdiNoteTooltip.jsx` | Floating system note tooltip rendering. |

## Boundary

- `EdiUnifiedCheckPanel.jsx` owns API calls, polling, selected detail state, and export flow.
- Components in this folder render EDI unified UI only and receive data/actions through props.
