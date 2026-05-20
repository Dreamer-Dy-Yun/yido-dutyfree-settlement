# TODO: router_tenant 분리 기반 생성

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- `router_tenant.py`를 바로 여러 라우터로 쪼개기 전에 schema/helper 공통 기반을 분리한다.

## 작업 범위

- 기존 `router_tenant.py`의 Pydantic schema와 route 공통 helper를 별도 파일로 이동한다.
- 기존 `router_tenant.py`는 `/api/tenant` prefix를 가진 aggregator 역할을 유지한다.
- 하위 라우터 분리 구현은 TODO-002~005에서 순차 수행한다.

## 선행 조건

- TODO-001 완료

## 수정 가능 파일

- `backend/WEB_SERVER/routers/router_tenant.py`

## 생성 가능 파일

- `backend/WEB_SERVER/routers/tenant_schemas.py`
- `backend/WEB_SERVER/routers/tenant_helpers.py`
- `mulAg/review/REVIEW-011.md`

## 읽기 전용 파일

- `backend/WEB_SERVER/routers/router_system_admin.py`
- `backend/WEB_SERVER/services/service_email.py`
- `backend/WEB_SERVER/routers/README.md`

## 수정 금지 파일

- `backend/WEB_SERVER/app.py`
- `frontend`
- `infra`
- `backend/DATABASE/dbms`

## 입력

- `router_tenant.py`의 schema class 목록
- `router_tenant.py`의 `_get_current_tenant_schema_from_user`, `_get_current_tenant_schemas`, verification helper, usage helper

## 출력

- `tenant_schemas.py`
- `tenant_helpers.py`
- import 경로가 정리된 `router_tenant.py`

## 작업 단계

- [ ] 1. Pydantic schema class를 `tenant_schemas.py`로 이동한다.
- [ ] 2. 공통 helper를 `tenant_helpers.py`로 이동한다.
- [ ] 3. `router_tenant.py`가 새 schema/helper 모듈을 import하도록 변경한다.
- [ ] 4. route 함수 이동은 하지 않는다.

## 완료 기준

- `router_tenant.py`의 route 함수 동작이 유지된다.
- schema/helper만 분리되고 endpoint path/method는 변경되지 않는다.
- TODO-002~005가 같은 helper/schema를 재사용할 수 있다.

## 주의사항

- 하위 라우터에 `/api/tenant` prefix를 중복 지정하지 않는다.
- 대형 route 이동은 후속 todo에서 순차 수행한다.
