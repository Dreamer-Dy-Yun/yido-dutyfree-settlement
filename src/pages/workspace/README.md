# Workspace Page Components

Tenant workspace subcomponents live here.

| File | Responsibility |
| --- | --- |
| `WorkspaceUsersSection.jsx` | User list table and user row actions. |
| `WorkspaceUsageSection.jsx` | Usage statistic cards. |
| `WorkspaceUserModal.jsx` | Create/edit tenant user form modal. |
| `WorkspaceDeleteConfirmModal.jsx` | Destructive user deletion confirmation modal. |

## Boundary

- `WorkspacePage.jsx` owns data loading, mutation handlers, and routing through `src/api/tenant/`.
- Components in this folder render workspace UI only and receive all data/actions through props.
