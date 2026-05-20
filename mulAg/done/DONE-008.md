# REVIEW: service_email verification/welcome template split

## Executed At

2026-05-20 14:16:58

## Reference Plan

- PLAN-20260520-backend-cleanup.md

## Reference TODO

- TODO-008.md

## Scope Performed

- Performed only the reduced first pass of TODO-008.
- Kept `EmailService.send()` implementation inside `service_email.py`.
- Kept the public `EmailService.set_verification_email(...) -> Self` chainable API.
- Kept the public `EmailService.set_welcome_email(...) -> Self` chainable API.
- Moved only verification and welcome MIME message builders to `email_templates.py`.
- Did not modify the other `set_xxx_email` template methods.

## Changed Files

- `backend/WEB_SERVER/services/service_email.py`

## Created Files

- `backend/WEB_SERVER/services/email_templates.py`

## Unchanged Files

- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`
- `backend/WEB_SERVER/app.py`
- `backend/WEB_SERVER/services/test_service_email.py`

## Validation

- Passed: `py -3 -m py_compile backend/WEB_SERVER/services/service_email.py backend/WEB_SERVER/services/email_templates.py`
- Removed generated `__pycache__` bytecode files created by the compile check because they are outside the allowed create-file scope.

## Remaining Templates

- `set_company_registration_email`
- `set_company_approval_email`
- `set_user_temp_password_email`
- `set_user_deletion_email`
- `set_company_rejection_email`
- `set_company_deletion_email`

## Remaining Issues

- SMTP transport split was not performed.
- DB SMTP account resolver split was not performed.
- `backend/WEB_SERVER/services/README.md` was not updated because it was outside this Sub-Agent's allowed write/create scope.

## QA Request

- Confirm that the changed and created files are inside the reduced TODO-008 ownership boundary.
- Confirm that `EmailService.set_xxx_email(...).send(...)` compatibility is preserved for the two moved templates.
