# REVIEW: router_system_admin_tenants 300라인 초과 해소

## 수행 일시

2026-05-20 14:15:56

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 참조한 todo

- TODO-012.md

## 수행 내용

- `router_system_admin_tenants.py`에서 테넌트 승인, 거부, 삭제 lifecycle 라우트를 분리했다.
- `TenantRejectionRequest`, `TenantDeletionRequest` schema를 lifecycle 전용 파일로 이동했다.
- `router_system_admin_tenants.py`는 테넌트 목록, 승인 대기 목록, 상세 조회, 정보 수정, 활성화, 비활성화 책임만 유지한다.
- `router_system_admin_tenants.py`가 `router_system_admin_tenant_lifecycle.py`를 하위 라우터로 include하도록 구성했다.
- `app.py`는 수정하지 않았고 기존 `/api/system-admin` prefix 등록 경로를 유지했다.

## 변경 파일

- `backend/WEB_SERVER/routers/router_system_admin_tenants.py`

## 생성 파일

- `backend/WEB_SERVER/routers/router_system_admin_tenant_lifecycle.py`
- `mulAg/review/REVIEW-012.md`

## 미변경 파일

- `backend/WEB_SERVER/routers/router_system_admin.py`
- `backend/WEB_SERVER/app.py`
- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/services/service_email.py`
- `backend/DATABASE`

## 검증 내용

- `router_system_admin_tenants.py`: 177라인
- `router_system_admin_tenant_lifecycle.py`: 205라인
- `py -3 -m py_compile D:\DEV\YIDO\backend\WEB_SERVER\routers\router_system_admin_tenants.py D:\DEV\YIDO\backend\WEB_SERVER\routers\router_system_admin_tenant_lifecycle.py` 통과

## 남은 이슈

- 테넌트 승인/거부/삭제 라우트는 여전히 이메일, DB schema 생성/삭제, 파일 삭제 책임을 직접 호출한다.
- 이번 TODO 범위는 300라인 초과 해소와 lifecycle 파일 분리이므로 서비스 추출은 수행하지 않았다.

## QA 확인 요청 사항

- `router_system_admin_tenants.py`와 `router_system_admin_tenant_lifecycle.py`가 각각 300라인 이하인지 확인 바란다.
- `app.py` 미수정 상태에서 기존 `/api/system-admin` 하위 경로가 유지되는지 확인 바란다.
- lifecycle 분리 후 `/tenants/pending`이 `/tenants/{tenant_id}`보다 먼저 선언된 상태가 유지되는지 확인 바란다.
