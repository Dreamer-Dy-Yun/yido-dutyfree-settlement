# Tenant Detail Components

System-admin tenant detail subcomponents live here.

| File | Responsibility |
| --- | --- |
| `TenantDetailReadView.jsx` | Read-only tenant detail sections. |
| `TenantDetailEditForm.jsx` | Tenant edit form sections. |
| `TenantRejectModal.jsx` | Rejection reason modal. |
| `TenantDeleteModal.jsx` | Deletion reason and confirmation modal. |

## Boundary

- `TenantDetailPage.jsx` owns data loading, mutation handlers, and navigation.
- Components in this folder render tenant detail UI only and receive data/actions through props.
