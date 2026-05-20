# Components

Shared tenant-facing shell and UI components live here.

| File | Responsibility |
| --- | --- |
| `DashboardShell.jsx` | Owns the tenant dashboard layout boundary: sidebar, session header, current-user refresh, logout, and optional admin-only redirect. |
| `SessionHeader.jsx` | Tenant session header wrapper around shared header/profile behavior. |
| `AppHeader.jsx` | Generic application header used by tenant and system-admin shells. |
| `Sidebar.jsx` | Tenant and system-admin navigation sidebar. |
| `CommonTabsRow.jsx` | Reusable tab row with optional right-side action slot. |
| `ProfileModal.jsx` | Shared profile/password modal. |

Page components should prefer `DashboardShell.jsx` instead of assembling `Sidebar` and `SessionHeader` directly.
