# REVIEW: TODO-017 email_user_templates 계정 템플릿 분리

## 수행 일시

2026-05-20 14:36:56

## 참조 plan

mulAg/plan/active/PLAN-20260520-backend-cleanup.md

## 참조한 todo

mulAg/todo/TODO-017.md

## 수행 내용

- `email_user_templates.py`에 남아 있던 tenant user 계정 관련 builder 2개를 분리했습니다.
- `build_user_temp_password_email`, `build_user_deletion_email`을 `email_user_account_templates.py`로 이동했습니다.
- `service_email.py`는 import 경로만 조정했습니다.
- `EmailService` 공개 API, `set_xxx_email(...).send(...)` 체이닝, `send()` 위치는 유지했습니다.

## 변경 파일

- backend/WEB_SERVER/services/service_email.py
- backend/WEB_SERVER/services/email_user_templates.py

## 생성 파일

- backend/WEB_SERVER/services/email_user_account_templates.py
- mulAg/review/REVIEW-017.md

## 미변경 파일

- backend/WEB_SERVER/routers/*
- backend/WEB_SERVER/app.py
- backend/DATABASE/*
- 테스트 파일

## 검증 내용

- ReadAllLines 기준 라인 수를 확인했습니다.
- `backend/WEB_SERVER/services/service_email.py`: 639 lines
- `backend/WEB_SERVER/services/email_user_templates.py`: 196 lines
- `backend/WEB_SERVER/services/email_user_account_templates.py`: 136 lines
- `service_email.py`, `email_user_templates.py`, `email_user_account_templates.py` 모두 `compile()` 문법 확인 통과했습니다.

## 남은 이슈

- `service_email.py`는 아직 300라인을 초과합니다. 회사 거부/삭제 템플릿 분리 TODO 범위로 남아 있습니다.

## QA 확인 요청 사항

- 허용 파일 범위 위반 여부를 확인해 주세요.
- `email_user_templates.py`와 `email_user_account_templates.py`가 ReadAllLines 기준 300라인 이하인지 확인해 주세요.
- `EmailService` 공개 API와 체이닝 동작이 유지되는지 확인해 주세요.
