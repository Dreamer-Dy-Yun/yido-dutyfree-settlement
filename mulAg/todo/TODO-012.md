# TODO: router_system_admin_tenants 300라인 초과 해소

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- TODO-006 결과물인 `router_system_admin_tenants.py`가 300라인을 초과한 문제를 해소한다.

## 작업 범위

- tenant 조회/수정 라우트와 approval/rejection/deletion 라우트를 책임 단위로 나눈다.
- `router_system_admin_tenants.py`는 aggregator 또는 tenant 조회/상태 변경 중심 파일로 축소한다.

## 선행 조건

- TODO-006 review 보류 상태
- `router_system_admin_tenants.py`가 생성되어 있음

## 수정 가능 파일

- `backend/WEB_SERVER/routers/router_system_admin.py`
- `backend/WEB_SERVER/routers/router_system_admin_tenants.py`

## 생성 가능 파일

- `backend/WEB_SERVER/routers/router_system_admin_tenant_lifecycle.py`
- `mulAg/review/REVIEW-012.md`

## 읽기 전용 파일

- `backend/WEB_SERVER/routers/router_system_admin_dashboard.py`
- `backend/WEB_SERVER/services/service_email.py`
- `backend/WEB_SERVER/services/service_tenant_deletion.py`

## 수정 금지 파일

- `backend/WEB_SERVER/app.py`
- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/services/service_email.py`
- `backend/DATABASE`

## 입력

- `router_system_admin_tenants.py`의 tenant approval/rejection/deletion 라우트
- QA 보류 사유: 새 파일 300라인 초과

## 출력

- 300라인 이하로 축소된 `router_system_admin_tenants.py`
- lifecycle 책임을 가진 `router_system_admin_tenant_lifecycle.py`
- `mulAg/review/REVIEW-012.md`

## 작업 단계

- [ ] 1. approval/rejection/deletion 라우트와 관련 request schema를 lifecycle 파일로 이동한다.
- [ ] 2. `router_system_admin_tenants.py`에 lifecycle 하위 라우터를 include하거나 aggregator 구조를 정리한다.
- [ ] 3. `/tenants/pending`이 `/tenants/{tenant_id}`보다 먼저 등록되는 순서를 유지한다.
- [ ] 4. 두 파일 모두 300라인 이하인지 확인한다.

## 완료 기준

- `router_system_admin_tenants.py`와 신규 lifecycle 파일이 각각 300라인 이하.
- `app.py` 변경 없이 기존 `/api/system-admin` 라우트 prefix가 유지됨.
- TODO-006 QA 보류 사유가 해소됨.

## 주의사항

- 이메일 발송, schema 생성/삭제, tenant deletion service 동작은 변경하지 않는다.
- API 응답 형식과 에러 처리 형식은 유지한다.
