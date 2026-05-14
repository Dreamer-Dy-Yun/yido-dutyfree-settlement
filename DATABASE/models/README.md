# DATABASE/models

This folder owns SQLAlchemy declarative models for public and tenant schemas.

## Files

| Path | Responsibility |
| --- | --- |
| `base_model.py` | Common declarative base with shared DB columns and helper serialization methods. |
| `public_model.py` | Public schema models: system admins, service accounts, tenants, LLM API keys, prompts, and test model. |
| `tenant_model.py` | Tenant schema models: users, OCR rows, verified/archive rows, images, EDI unified rows, matching rows, vendor EDI rows, and LLM usage. |
| `__init__.py` | Re-exports all active model classes for `from DATABASE import models` usage. |

## Boundary Notes

- Model names and columns are API/DB contract inputs. Do not rename or split without checking repository, router, processor, and test imports.
- `tenant_model.py` is large but schema-contract-heavy. Split only with compatibility re-exports and migration/import checks.
- DB constraints should stay in models/DB, not be replaced by router-only validation.
