# REVIEW: EmailService 사용자 템플릿 builder 분리

## 수행 일시

2026-05-20 14:31:07

## 참조 plan

mulAg/plan/active/PLAN-20260520-backend-cleanup.md

## 참조한 todo

mulAg/todo/TODO-014.md

## 수행 내용

- `set_user_temp_password_email` 본문 생성 책임을 `build_user_temp_password_email`로 분리했습니다.
- `set_user_deletion_email` 본문 생성 책임을 `build_user_deletion_email`로 분리했습니다.
- `EmailService` 공개 메서드명, 매개변수, `Self` 반환, `set_xxx_email(...).send(...)` 체이닝 계약을 유지했습니다.
- `EmailService.send()` 구현 위치와 SMTP 전송 경로는 변경하지 않았습니다.
- `email_user_templates.py`가 300라인을 넘지 않도록 builder 선언부를 압축했습니다.

## 변경 파일

- backend/WEB_SERVER/services/service_email.py
- backend/WEB_SERVER/services/email_user_templates.py

## 생성 파일

- mulAg/review/REVIEW-014.md

## 미변경 파일

- backend/WEB_SERVER/routers/*
- backend/WEB_SERVER/app.py
- backend/DATABASE/*
- 테스트 파일

## 라인 수

- backend/WEB_SERVER/services/service_email.py: 593 lines
- backend/WEB_SERVER/services/email_user_templates.py: 296 lines

## 검증 내용

- `py -3 -c "compile(...)"` 방식으로 `service_email.py`, `email_user_templates.py` 문법 확인 통과.
- `py_compile`은 `__pycache__` 생성을 피하기 위해 사용하지 않았습니다.

## 남은 이슈

- `service_email.py`는 아직 593라인입니다. 남은 회사 거부/삭제 템플릿 분리는 별도 TODO 범위로 남겨야 합니다.
- `email_user_templates.py`의 기존 verification/welcome subject 문자열에 `????` 형태의 mojibake가 남아 있습니다. 이번 TODO 범위가 아닌 기존 상태라 수정하지 않았습니다.
- 최초 TODO-014 문서에는 `email_user_templates.py`가 수정 가능 파일로 명시되지 않았습니다. Orchestrator가 QA 보류 후 TODO-014 권한 범위를 실제 사용자 템플릿 파일 기준으로 보정했습니다.

## QA 확인 요청 사항

- TODO-014의 허용 수정 파일 범위 준수 여부 확인.
- 두 사용자 템플릿만 builder로 분리되었는지 확인.
- `EmailService` 공개 API, 체이닝 반환, `send()` 위치 유지 여부 확인.
