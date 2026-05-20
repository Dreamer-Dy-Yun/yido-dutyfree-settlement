# REVIEW: TODO-002 tenant user/usage/info router split

## 수행 일시

2026-05-20 14:51:12

## 참조 plan

mulAg/plan/active/PLAN-20260520-backend-cleanup.md

## 참조한 todo

mulAg/todo/TODO-002.md

## 수행 내용

- `router_tenant.py`의 `/users`, `/usage`, `/usage/users/{user_id}/tokens`, `/info` 라우트를 `router_tenant_users.py`로 이동했습니다.
- `router_tenant.py`는 `/api/tenant` prefix를 가진 aggregator로 유지하고 `tenant_users_router`를 include하도록 변경했습니다.
- 하위 라우터에는 `/api/tenant` prefix를 지정하지 않았습니다.
- 기존 path, method, summary, description, response payload 구조를 유지했습니다.

## 변경 파일

- backend/WEB_SERVER/routers/router_tenant.py

## 생성 파일

- backend/WEB_SERVER/routers/router_tenant_users.py
- mulAg/review/REVIEW-002.md

## 미변경 파일

- backend/WEB_SERVER/app.py
- backend/WEB_SERVER/routers/router_system_admin.py
- backend/WEB_SERVER/services/service_email.py
- backend/DATABASE 이하

## 검증 내용

- `router_tenant.py`, `router_tenant_users.py`에 대해 Python compile 문법 확인을 수행했습니다.
- 신규 라우터는 `router = APIRouter()` 형태로 `/api/tenant` prefix를 중복 지정하지 않았습니다.
- ReadAllLines 기준 라인 수: `router_tenant.py` 1972, `router_tenant_users.py` 280.

## 남은 이슈

- `router_tenant.py`에는 EDI, OCR, 매칭, 검수 라우트가 남아 있어 후속 TODO-003~005 분리가 필요합니다.
- 신규 `router_tenant_users.py`는 ReadAllLines 기준 300라인 이하입니다.

## QA 확인 요청 사항

- `router_tenant.py` aggregator include 위치가 의도한 라우트 등록 방식과 일치하는지 확인해 주세요.
- 사용자/사용량/테넌트 정보 라우트의 path/method가 기존과 동일하게 유지되었는지 확인해 주세요.
