# TODO: router_system_admin tenant lifecycle 라우트 분리

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- `router_system_admin.py`를 aggregator로 유지하면서 dashboard/tenant lifecycle 관련 라우트를 하위 라우터로 분리한다.

## 작업 범위

- 분리 대상 endpoint:
  - `GET /api/system-admin/dashboard/stats`
  - `GET /api/system-admin/tenants`
  - `GET /api/system-admin/tenants/{tenant_id}`
  - `GET /api/system-admin/tenants/pending`
  - `POST /api/system-admin/tenants/{tenant_id}/approve`
  - `POST /api/system-admin/tenants/{tenant_id}/reject`
  - `PUT /api/system-admin/tenants/{tenant_id}`
  - `POST /api/system-admin/tenants/{tenant_id}/activate`
  - `POST /api/system-admin/tenants/{tenant_id}/deactivate`
  - `DELETE /api/system-admin/tenants/{tenant_id}`

## 선행 조건

- 없음

## 수정 가능 파일

- `backend/WEB_SERVER/routers/router_system_admin.py`

## 생성 가능 파일

- `backend/WEB_SERVER/routers/router_system_admin_dashboard.py`
- `backend/WEB_SERVER/routers/router_system_admin_tenants.py`
- `mulAg/review/REVIEW-006.md`

## 읽기 전용 파일

- `backend/WEB_SERVER/services/auth_service.py`
- `backend/WEB_SERVER/services/verification_token.py`
- `backend/WEB_SERVER/routers/tenant_schemas.py`

## 수정 금지 파일

- `backend/DATABASE/dbms/postgre/lagacy/pg_manager.py`
- `backend/PROCESSOR_DATA`
- `backend/WEB_SERVER/app.py`

## 입력

- 소스 라우터 라인: 138-526
- 핵심 라우트 이름:
  - get_system_stats
  - get_tenants
  - get_tenant_detail
  - get_pending_tenants
  - approve_tenant
  - reject_tenant
  - update_tenant
  - activate_tenant
  - deactivate_tenant
  - delete_tenant

## 출력

- `backend/WEB_SERVER/routers/router_system_admin_dashboard.py`
- `backend/WEB_SERVER/routers/router_system_admin_tenants.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`(해당 라우트 제거)

## 작업 단계

- [ ] 1. dashboard 라우트를 `router_system_admin_dashboard.py`로 이동.
- [ ] 2. tenant lifecycle 라우트를 `router_system_admin_tenants.py`로 이동.
- [ ] 3. 기존 `router_system_admin.py`는 하위 라우터를 include하는 aggregator로 축소.
- [ ] 4. `/tenants/pending` 같은 static route가 `/tenants/{tenant_id}`보다 먼저 등록되도록 정렬.

## 완료 기준

- dashboard 1개와 tenant lifecycle 라우트 9개가 분리 라우터로만 존재.
- 기존 권한/검증/DB 접근 동작이 변경되지 않음.
- `backend/WEB_SERVER/app.py` 변경 없이 기존 `router_system_admin` include 경로가 유지됨.

## 주의사항

- tenant 삭제는 실제 DB/ZIP/아카이브 정리가 포함될 수 있어 실패 처리 형태를 숨기지 않는다.
