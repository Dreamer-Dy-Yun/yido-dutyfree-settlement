# REVIEW: EmailService 회사 등록/승인 템플릿 builder 분리

## 수행 일시

2026-05-20 14:21:43

## 참조 plan

mulAg/plan/active/PLAN-20260520-backend-cleanup.md

## 참조한 todo

TODO-013

## 수행 내용

- `EmailService.set_company_registration_email`의 MIME 생성 본문을 `build_company_registration_email` builder로 분리했습니다.
- `EmailService.set_company_approval_email`의 MIME 생성 본문을 `build_company_approval_email` builder로 분리했습니다.
- `EmailService` 공개 메서드명, 인자, 반환 타입, 체이닝 방식은 유지했습니다.
- `EmailService.send()` 구현 위치와 SMTP 전송 책임은 변경하지 않았습니다.

## 변경 파일

- D:\DEV\YIDO\backend\WEB_SERVER\services\service_email.py
- D:\DEV\YIDO\backend\WEB_SERVER\services\email_templates.py

## 생성 파일

- D:\DEV\YIDO\mulAg\review\REVIEW-013.md

## 미변경 파일

- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant.py
- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_system_admin.py
- D:\DEV\YIDO\backend\WEB_SERVER\app.py
- D:\DEV\YIDO\backend\DATABASE
- 테스트 파일

## 검증 내용

다음 두 파일을 `compile()`로 문법 확인했습니다.

```text
OK backend\WEB_SERVER\services\service_email.py
OK backend\WEB_SERVER\services\email_templates.py
```

`py_compile`은 `__pycache__` 부산물을 만들 수 있어 사용하지 않았습니다.

## 남은 이슈

- `service_email.py`에는 아직 `set_user_temp_password_email`, `set_user_deletion_email`, `set_company_rejection_email`, `set_company_deletion_email` 템플릿 본문이 남아 있습니다.
- 이번 TODO 범위는 회사 등록/승인 템플릿 2개만 분리하는 것이므로 추가 템플릿은 후속 TODO로 분리해야 합니다.

## QA 확인 요청 사항

- `EmailService.set_company_registration_email(...).send(...)` 체이닝 API가 유지되었는지 확인해 주세요.
- `EmailService.set_company_approval_email(...).send(...)` 체이닝 API가 유지되었는지 확인해 주세요.
- 금지 파일 수정이 없는지 확인해 주세요.
