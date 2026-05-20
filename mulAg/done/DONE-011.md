# REVIEW: router_tenant schema/helper 기반 분리

## 수행 일시

2026-05-20 13:58:22

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 참조한 todo

- TODO-011.md

## 수행 내용

- `router_tenant.py` 내부의 Pydantic request/response schema class를 `tenant_schemas.py`로 분리했다.
- `router_tenant.py` 내부의 tenant schema 조회, verification upsert/merge, usage count, tenant info response 공통 helper를 `tenant_helpers.py`로 분리했다.
- `router_tenant.py`는 기존 `/api/tenant` prefix와 route function 위치를 유지하고, 분리된 schema/helper만 import하도록 정리했다.
- endpoint path/method, route decorator, route function 이동은 수행하지 않았다.

## 변경 파일

- `backend/WEB_SERVER/routers/router_tenant.py`

## 생성 파일

- `backend/WEB_SERVER/routers/tenant_schemas.py`
- `backend/WEB_SERVER/routers/tenant_helpers.py`
- `mulAg/review/REVIEW-011.md`

## 미변경 파일

- `backend/WEB_SERVER/app.py` - 본 TODO에서는 수정하지 않음. 작업트리에는 기존/타 작업자 변경이 남아 있음.
- `backend/WEB_SERVER/routers/router_system_admin.py` - 본 TODO에서는 수정하지 않음. 작업트리에는 기존/타 작업자 변경이 남아 있음.
- `backend/WEB_SERVER/services/service_email.py` - 본 TODO에서 수정하지 않음.
- `backend/DATABASE` - 본 TODO에서 수정하지 않음.

## 검증 내용

- `py -m py_compile backend/WEB_SERVER/routers/router_tenant.py backend/WEB_SERVER/routers/tenant_schemas.py backend/WEB_SERVER/routers/tenant_helpers.py` 통과.
- `python -m py_compile ...`는 WindowsApps `python.exe` alias가 실제 Python 실행기로 동작하지 않아 사용할 수 없었고, Windows Python launcher `py`로 동일 검증을 수행했다.
- `git status --short` 기준 본 TODO 산출물은 `router_tenant.py`, `tenant_schemas.py`, `tenant_helpers.py`, `REVIEW-011.md`다.
- 동일 상태 확인에서 `app.py`, `router_system_admin.py`의 기존/타 작업자 변경이 함께 보였으나, 본 TODO에서는 해당 파일을 수정하지 않았다.

## 남은 이슈

- `router_tenant.py`의 route function은 아직 한 파일에 남아 있으며, TODO-002~005에서 순차적으로 분리해야 한다.
- `tenant_schemas.py`는 기존 schema 기본값을 유지하기 위해 list 기본값도 그대로 옮겼다. 후속 하드닝에서 `Field(default_factory=...)` 전환 여부를 별도로 판단할 수 있다.
- `tenant_helpers.py`의 verification helper는 DB 쓰기 helper를 포함한다. 후속 route 분리 시 read-only helper와 mutation helper를 더 세분화할 수 있다.

## QA 확인 요청 사항

- route function 이동 없이 schema/helper만 분리되었는지 확인 요청.
- `app.py`, `router_system_admin.py`, `service_email.py`, `DATABASE` 미수정 여부 확인 요청.
- TODO-002~005 후속 분리에서 `tenant_schemas.py`, `tenant_helpers.py`를 공통 기반으로 사용해도 되는지 확인 요청.
