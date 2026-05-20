# TODO: service_email 임시비밀번호/삭제 템플릿 분리

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- `service_email.py`에 남은 사용자 임시비밀번호/삭제 메일 템플릿을 `email_templates.py`로 분리한다.

## 작업 범위

- `set_user_temp_password_email`
- `set_user_deletion_email`

## 선행 조건

- TODO-013 done

## 수정 가능 파일

- `backend/WEB_SERVER/services/service_email.py`
- `backend/WEB_SERVER/services/email_user_templates.py`

## 생성 가능 파일

- `mulAg/review/REVIEW-014.md`

## 읽기 전용 파일

- `backend/WEB_SERVER/services/test_service_email.py`
- `mulAg/done/DONE-013.md`
- `backend/WEB_SERVER/services/email_templates.py`

## 수정 금지 파일

- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`
- `backend/WEB_SERVER/app.py`
- `backend/DATABASE`

## 입력

- 기존 `set_user_temp_password_email` 구현
- 기존 `set_user_deletion_email` 구현
- `email_templates.py`의 기존 builder 패턴

## 출력

- 분리된 사용자 임시비밀번호/삭제 템플릿 builder
- 공개 API를 유지하는 `EmailService` wrapper
- `REVIEW-014.md`

## 작업 단계

- [ ] 1. 두 템플릿을 `email_templates.py` builder 함수로 이동.
- [ ] 2. `EmailService` 메서드는 기존 시그니처/체이닝 반환을 유지.
- [ ] 3. 검증 결과를 review에 기록.

## 완료 기준

- 두 사용자 템플릿 본문이 `service_email.py`에서 제거됨.
- 기존 체이닝 API가 유지됨.
- `service_email.py`가 300라인 이하에 가까워짐.

## 주의사항

- TODO-013 완료 전 수행하지 않는다.
