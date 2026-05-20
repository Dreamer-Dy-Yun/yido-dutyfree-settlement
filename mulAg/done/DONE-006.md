# REVIEW: router_system_admin tenant lifecycle 라우트 분리

## 수행 일시

2026-05-20 13:58:43

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 참조한 todo

- TODO-006.md

## 수행 내용

- `router_system_admin.py`를 `app.py` 변경 없이 기존 `/api/system-admin` aggregator로 유지했습니다.
- dashboard 통계 라우트를 `router_system_admin_dashboard.py`로 이동했습니다.
- tenant lifecycle 라우트를 `router_system_admin_tenants.py`로 이동했습니다.
- aggregator가 `dashboard_router`, `tenants_router`를 include하도록 변경했습니다.
- `router_system_admin_tenants.py`에서 `/tenants/pending` static route를 `/tenants/{tenant_id}` dynamic route보다 먼저 선언했습니다.
- service account, LLM API key, prompt 라우트는 원본 파일에 그대로 유지했습니다.

## 변경 파일

- `backend/WEB_SERVER/routers/router_system_admin.py`

## 생성 파일

- `backend/WEB_SERVER/routers/router_system_admin_dashboard.py`
- `backend/WEB_SERVER/routers/router_system_admin_tenants.py`
- `mulAg/review/REVIEW-006.md`

## 미변경 파일

- `backend/WEB_SERVER/app.py`
- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/services/service_email.py`
- `backend/DATABASE`

## 검증 내용

- `rg`로 `router_system_admin.py`에 dashboard/tenant lifecycle route decorator가 남지 않았고, service-account 이후 route만 남은 것을 확인했습니다.
- `rg`로 `router_system_admin_dashboard.py`에 `/dashboard/stats` route가 존재하는 것을 확인했습니다.
- `rg`로 `router_system_admin_tenants.py`에서 `/tenants/pending`이 `/tenants/{tenant_id}`보다 앞에 선언된 것을 확인했습니다.
- `py -3` 기반 `compile(...)`로 세 Python 파일의 문법 검사를 통과했습니다.

## 남은 이슈

- `router_system_admin_tenants.py`는 362라인입니다. TODO-006의 생성 가능 파일이 tenant router 1개로 제한되어 있어 추가 분할은 수행하지 않았습니다. 300라인 기준을 엄격히 적용하려면 후속 TODO에서 tenant approval/rejection/deletion 책임을 서비스 또는 추가 라우터로 분리해야 합니다.
- `router_system_admin.py`는 service account, LLM API key, prompt 라우트가 남아 570라인입니다. 이는 TODO-007 범위로 남겨야 합니다.

## QA 확인 요청 사항

- `app.py` 변경 없이 기존 `router_system_admin` include 경로가 유지되는지 확인해 주세요.
- `/tenants/pending` static route가 dynamic route보다 먼저 등록된 상태를 확인해 주세요.
- TODO-006 권한 범위 밖 파일 변경이 없는지 확인해 주세요.
