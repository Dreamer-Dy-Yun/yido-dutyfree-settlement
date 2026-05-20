# TODO: service_email 회사 등록/승인 템플릿 분리

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- `service_email.py`에 남은 긴 템플릿 중 회사 등록/승인 메일 템플릿을 `email_templates.py`로 분리한다.

## 작업 범위

- `set_company_registration_email`
- `set_company_approval_email`

## 선행 조건

- TODO-008 부분 완료

## 수정 가능 파일

- `backend/WEB_SERVER/services/service_email.py`
- `backend/WEB_SERVER/services/email_templates.py`

## 생성 가능 파일

- `mulAg/review/REVIEW-013.md`

## 읽기 전용 파일

- `backend/WEB_SERVER/services/test_service_email.py`
- `mulAg/review/REVIEW-008.md`

## 수정 금지 파일

- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`
- `backend/WEB_SERVER/app.py`
- `backend/DATABASE`

## 입력

- 기존 `set_company_registration_email` 구현
- 기존 `set_company_approval_email` 구현
- `email_templates.py`의 기존 builder 패턴

## 출력

- 분리된 회사 등록/승인 템플릿 builder
- 공개 API를 유지하는 `EmailService` wrapper
- `REVIEW-013.md`

## 작업 단계

- [ ] 1. 두 템플릿을 `email_templates.py` builder 함수로 이동.
- [ ] 2. `EmailService` 메서드는 기존 시그니처/체이닝 반환을 유지.
- [ ] 3. `send()`와 DB resolver는 수정하지 않음.
- [ ] 4. 검증 결과를 review에 기록.

## 완료 기준

- 회사 등록/승인 템플릿 본문이 `service_email.py`에서 제거됨.
- `EmailService.set_company_registration_email(...).send(...)`와 `set_company_approval_email(...).send(...)` 사용 방식 유지.
- 기능 코드 외 파일 수정 없음.

## 주의사항

- 같은 `service_email.py`를 다루는 다른 email todo와 병렬 구현 금지.
