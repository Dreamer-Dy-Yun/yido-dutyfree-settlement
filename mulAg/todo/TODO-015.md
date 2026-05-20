# TODO: service_email 회사 거부/삭제 템플릿 분리

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- `service_email.py`에 남은 회사 거부/삭제 메일 템플릿을 `email_company_templates.py`로 분리한다.

## 작업 범위

- `set_company_rejection_email`
- `set_company_deletion_email`

## 선행 조건

- TODO-014 done

## 수정 가능 파일

- `backend/WEB_SERVER/services/service_email.py`
- `backend/WEB_SERVER/services/email_company_templates.py`

## 생성 가능 파일

- `mulAg/review/REVIEW-015.md`

## 읽기 전용 파일

- `backend/WEB_SERVER/services/test_service_email.py`
- `mulAg/done/DONE-014.md`
- `backend/WEB_SERVER/services/email_templates.py`

## 수정 금지 파일

- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`
- `backend/WEB_SERVER/app.py`
- `backend/DATABASE`

## 입력

- 기존 `set_company_rejection_email` 구현
- 기존 `set_company_deletion_email` 구현
- `email_company_templates.py`의 기존 builder 패턴

## 출력

- 분리된 회사 거부/삭제 템플릿 builder
- 공개 API를 유지하는 `EmailService` wrapper
- `REVIEW-015.md`

## 작업 단계

- [ ] 1. 두 템플릿을 `email_company_templates.py` builder 함수로 이동.
- [ ] 2. `EmailService` 메서드는 기존 시그니처/체이닝 반환을 유지.
- [ ] 3. 검증 결과를 review에 기록.

## 완료 기준

- 모든 메일 템플릿 본문이 도메인별 email template 파일로 이동됨.
- `service_email.py`는 transport/facade/DB resolver 중심으로 축소됨.
- TODO-008 전체 보류 사유가 해소됨.

## 주의사항

- TODO-014 완료 전 수행하지 않는다.
