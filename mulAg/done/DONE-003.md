# REVIEW: TODO-003 EDI upload/unified/export router split

## 수행 일시

2026-05-20 15:02:32

## 참조 plan

mulAg/plan/active/PLAN-20260520-backend-cleanup.md

## 참조한 todo

mulAg/todo/TODO-003.md

## 수행 내용

- `router_tenant.py`를 `/api/tenant` prefix를 가진 aggregator로 유지했습니다.
- EDI upload, EDI unified enqueue/job/internal-run/export/groups/detail 라우트를 `router_tenant_edi.py`로 이동했습니다.
- `router_tenant_edi.py`는 `APIRouter()`만 사용하며 `/api/tenant` prefix를 중복 지정하지 않았습니다.
- `router_tenant.py`에서 `tenant_edi_router`를 include하도록 연결했습니다.
- `request_match_attempt`는 matching 책임이므로 `router_tenant.py`에 유지했습니다.
- 작업 중 스크립트 오류로 `router_tenant.py`가 손상되어, `HEAD` 원본 라우트 본문과 현재 분리 모듈 계약(`tenant_helpers.py`, `tenant_schemas.py`, `router_tenant_users.py`)을 기준으로 aggregator 상태를 재구성했습니다.

## 변경 파일

- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant.py

## 생성 파일

- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant_edi.py
- D:\DEV\YIDO\mulAg\review\REVIEW-003.md

## 미변경 파일

- D:\DEV\YIDO\backend\WEB_SERVER\app.py
- D:\DEV\YIDO\backend\WEB_SERVER\services\service_email.py
- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_system_admin.py
- D:\DEV\YIDO\backend\DATABASE

## 라인 수

- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant.py: 1547 lines
- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant_edi.py: 463 lines

## 검증 내용

- `py -3 -m py_compile backend\WEB_SERVER\routers\router_tenant.py backend\WEB_SERVER\routers\router_tenant_edi.py` 통과.
- `router_tenant.py`에 `router.include_router(tenant_edi_router)` 존재 확인.
- `router_tenant_edi.py`에 `/data-mapping/edi-upload`, `/data-mapping/edi-unified/run` 존재 확인.
- `request_match_attempt`는 `router_tenant.py`에 남아 있음 확인.
- `py_compile` 부산물인 `router_tenant*.pyc`는 제거했습니다.

## 남은 이슈

- `router_tenant_edi.py`는 ReadAllLines 기준 463라인으로 300라인 기준을 초과합니다.
- 이번 TODO의 생성 가능 파일이 `router_tenant_edi.py` 하나로 제한되어 추가 분리는 수행하지 않았습니다.
- 후속 TODO에서 EDI upload/job/export/groups를 더 작은 하위 라우터 또는 서비스 단위로 분리하는 것이 필요합니다.
- `router_tenant.py`는 아직 1547라인으로 큽니다. TODO-004/TODO-005 범위의 mapping/verification 분리가 이어져야 합니다.

## QA 확인 요청 사항

- EDI 라우트 이동 후 공개 path/method가 유지되는지 확인해 주세요.
- `/api/tenant` prefix가 하위 라우터에서 중복되지 않는지 확인해 주세요.
- `request_match_attempt`가 matching 책임으로 `router_tenant.py`에 유지된 것이 TODO 범위와 맞는지 확인해 주세요.
- `router_tenant_edi.py` 300라인 초과를 후속 TODO 대상으로 처리할지 판단해 주세요.
