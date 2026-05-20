# REVIEW: email_templates 도메인별 분리

## 수행 일시

2026-05-20 14:25:55

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 참조한 todo

- TODO-016.md

## 수행 내용

- `email_templates.py`에 모여 있던 builder 4개를 도메인별 파일로 분리했다.
- verification/welcome builder는 `email_user_templates.py`로 이동했다.
- company registration/approval builder는 `email_company_templates.py`로 이동했다.
- 공통 `MIMEMultipart("alternative")` 생성 책임은 `email_message_builder.py`로 분리했다.
- `email_templates.py`는 기존 import 경로 호환을 위한 re-export 모듈로 축소했다.
- `service_email.py`는 새 사용자/회사 템플릿 모듈을 직접 import하도록 조정했다.
- `EmailService` 공개 메서드, 체이닝 반환, `send()` 위치, SMTP/DB resolver 동작은 변경하지 않았다.

## 변경 파일

- `backend/WEB_SERVER/services/service_email.py`
- `backend/WEB_SERVER/services/email_templates.py`

## 생성 파일

- `backend/WEB_SERVER/services/email_user_templates.py`
- `backend/WEB_SERVER/services/email_company_templates.py`
- `backend/WEB_SERVER/services/email_message_builder.py`
- `mulAg/review/REVIEW-016.md`

## 미변경 파일

- `backend/WEB_SERVER/routers`
- `backend/WEB_SERVER/app.py`
- `backend/DATABASE`
- `backend/WEB_SERVER/services/test_service_email.py`

## 라인 수

- `backend/WEB_SERVER/services/service_email.py`: 888 lines
- `backend/WEB_SERVER/services/email_templates.py`: 20 lines
- `backend/WEB_SERVER/services/email_user_templates.py`: 196 lines
- `backend/WEB_SERVER/services/email_company_templates.py`: 262 lines
- `backend/WEB_SERVER/services/email_message_builder.py`: 26 lines

## 검증 내용

- `compile()` 기반 문법 확인 통과:
  - `backend/WEB_SERVER/services/service_email.py`
  - `backend/WEB_SERVER/services/email_templates.py`
  - `backend/WEB_SERVER/services/email_user_templates.py`
  - `backend/WEB_SERVER/services/email_company_templates.py`
  - `backend/WEB_SERVER/services/email_message_builder.py`
- `py_compile`은 `__pycache__` 생성을 피하기 위해 사용하지 않았다.

## 남은 이슈

- `service_email.py`는 아직 300라인을 초과한다. 다만 TODO-016의 직접 목표는 `email_templates.py` 초과 문제 해소이며, 남은 긴 템플릿 4개는 TODO-014/TODO-015 범위로 남아 있다.
- `email_templates.py`는 호환 re-export 역할만 하므로, 후속 정리에서 외부 참조가 모두 새 도메인 모듈로 이동되면 제거 여부를 검토할 수 있다.

## QA 확인 요청 사항

- `email_templates.py`, `email_user_templates.py`, `email_company_templates.py`, `email_message_builder.py`가 모두 300라인 이하인지 확인 요청.
- `service_email.py`의 공개 API와 `send()` 위치가 유지되었는지 확인 요청.
- 금지 파일인 router/app/DATABASE 미수정 여부 확인 요청.
