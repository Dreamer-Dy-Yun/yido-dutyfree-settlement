# TODO: service_email 템플릿/전송 책임 분리

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- `WEB_SERVER/services/service_email.py`의 공개 체이닝 API를 유지하면서 1차로 이메일 템플릿 빌더 책임만 분리한다.

## 작업 범위

- `EmailService.set_xxx_email(...).send(...)` 체이닝 계약을 유지한다.
- `service_email.py`의 템플릿 문자열/메시지 생성 책임을 `email_templates.py`로 분리한다.
- SMTP transport와 DB account resolver 분리는 후속 todo로 남긴다.

## 선행 조건

- 없음(단, TODO-001, TODO-002~007 완료와 무관)

## 수정 가능 파일

- `backend/WEB_SERVER/services/service_email.py`

## 생성 가능 파일

- `backend/WEB_SERVER/services/email_templates.py`
- `mulAg/review/REVIEW-008.md`

## 읽기 전용 파일

- `backend/WEB_SERVER/services/auth_service.py`
- `backend/WEB_SERVER/services/company_service.py`
- `backend/WEB_SERVER/services/verification_token.py`

## 수정 금지 파일

- `backend/WEB_SERVER/services/test_service_email.py` (테스트 계약 반영 전 임의 변경 금지)
- `backend/WEB_SERVER/services/test_queue_services.py`
- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`

## 입력

- 소스 코드: `backend/WEB_SERVER/services/service_email.py`
- 클래스: `EmailService`
- 템플릿 메서드:
  - set_verification_email
  - set_welcome_email
  - set_company_registration_email
  - set_company_approval_email
  - set_user_temp_password_email
  - set_user_deletion_email
  - set_company_rejection_email
  - set_company_deletion_email

## 출력

- `backend/WEB_SERVER/services/email_templates.py`
- `backend/WEB_SERVER/services/service_email.py`의 템플릿 책임 축소 및 공개 인터페이스 호환 유지

## 작업 단계

- [ ] 1. 템플릿 생성 책임을 `email_templates.py`로 추출.
- [ ] 2. 공통 MIME 메시지 생성 함수를 도입.
- [ ] 3. 기존 `EmailService` 공개 메서드는 wrapper로 유지.
- [ ] 4. 기존 `email_service`, `get_db_smtp_email_service` import 경로 유지.
- [ ] 5. SMTP transport와 DB resolver는 변경하지 않음.

## 완료 기준

- 모든 `set_xxx_email` 공개 메서드의 함수 시그니처와 반환값(`Self`)이 유지됨.
- 기존 사용처에서 `EmailService`, `email_service`, `get_db_smtp_email_service` import 방식이 유지됨.
- `service_email.py`에서 긴 템플릿 본문 책임이 제거됨.

## 주의사항

- fake success 응답을 추가하지 않는다.
- 인증 메일/초대 메일/승인 메일 실패 경로는 기존 예외/실패 동작으로 보존한다.
- `smtplib.SMTP` monkeypatch 테스트가 깨지지 않도록 `send()` 구현 위치는 유지한다.
