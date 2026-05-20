# Styles

Shared CSS with cross-feature ownership lives here.

| File | Responsibility |
| --- | --- |
| `appLayout.css` | Shared sidebar/header application layout classes such as `app-layout`, `app-main`, and `app-content`. |
| `commonUi.css` | Shared cards, buttons, tabs, tables, toolbars, and common state styles. |

Feature-specific CSS should stay with the feature or page. Do not place admin-only or tenant-only styles here unless the class is intentionally shared.
