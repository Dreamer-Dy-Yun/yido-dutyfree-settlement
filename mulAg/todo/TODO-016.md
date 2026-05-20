# TODO: email_templates 도메인별 분리

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- `email_templates.py`가 300라인을 초과한 문제를 해소하고, 사용자/회사 템플릿 책임을 파일 단위로 분리한다.

## 작업 범위

- 기존 `email_templates.py`의 공통 MIME 생성 함수는 유지하거나 `email_message_builder.py`로 분리한다.
- 사용자 템플릿과 회사 템플릿을 별도 파일로 나눈다.
- `service_email.py` import 경로를 새 파일 구조에 맞게 정리한다.

## 선행 조건

- TODO-013 done

## 수정 가능 파일

- `backend/WEB_SERVER/services/service_email.py`
- `backend/WEB_SERVER/services/email_templates.py`

## 생성 가능 파일

- `backend/WEB_SERVER/services/email_user_templates.py`
- `backend/WEB_SERVER/services/email_company_templates.py`
- `backend/WEB_SERVER/services/email_message_builder.py`
- `mulAg/review/REVIEW-016.md`

## 읽기 전용 파일

- `mulAg/done/DONE-013.md`
- `backend/WEB_SERVER/services/test_service_email.py`

## 수정 금지 파일

- `backend/WEB_SERVER/routers`
- `backend/WEB_SERVER/app.py`
- `backend/DATABASE`

## 입력

- 현재 `email_templates.py`의 builder 함수들
- `service_email.py`의 import/use 지점

## 출력

- 300라인 이하의 email template 관련 파일들
- 기존 `EmailService` 공개 API 유지
- `REVIEW-016.md`

## 작업 단계

- [ ] 1. 공통 MIME 생성 함수를 분리 또는 유지할 위치 결정.
- [ ] 2. verification/welcome 등 사용자 계열 템플릿을 `email_user_templates.py`로 이동.
- [ ] 3. company registration/approval 등 회사 계열 템플릿을 `email_company_templates.py`로 이동.
- [ ] 4. `service_email.py` import 경로를 정리.
- [ ] 5. 관련 파일 라인 수와 문법 검증 결과를 review에 기록.

## 완료 기준

- `email_templates.py`와 신규 템플릿 파일들이 각각 300라인 이하.
- 기존 `EmailService.set_xxx_email(...).send(...)` 체이닝 계약 유지.
- send/SMTP/DB resolver 동작 변경 없음.

## 주의사항

- 아직 이동하지 않은 4개 템플릿은 TODO-014/015에서 계속 처리한다.
