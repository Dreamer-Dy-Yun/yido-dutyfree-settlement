# app

This folder is a legacy or alternate FastAPI scaffold. The active backend service uses `WEB_SERVER/`.

## Files

| Path | Responsibility |
| --- | --- |
| `main.py` | Alternate FastAPI template app. Not registered by the active runtime entry point. |
| `config.py` | Template settings object. |

## Subfolders

| Path | Responsibility |
| --- | --- |
| `core/` | Template exception/security helpers. |
| `models/` | Template model definitions. |
| `schemas/` | Template Pydantic schemas. |

## Boundary Notes

- Do not extend this scaffold for active backend features unless the runtime decision changes.
- Prefer `WEB_SERVER/`, `DATABASE/`, and processor folders for production work.
