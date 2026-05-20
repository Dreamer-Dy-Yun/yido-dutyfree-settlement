# REVIEW: router_tenant_edi 300라인 초과 해소

## 수행 일시

2026-05-20 15:06:01

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 참조한 todo

- TODO-018.md

## 수행 내용

- `router_tenant_edi.py`를 EDI 라우터 aggregator로 축소했습니다.
- upload/job/run/status 라우트를 `router_tenant_edi_jobs.py`로 분리했습니다.
- export/groups/detail 라우트를 `router_tenant_edi_exports.py`로 분리했습니다.
- 하위 라우터는 `APIRouter()`만 사용하고 `/api/tenant` prefix는 추가하지 않았습니다.
- `request_match_attempt`는 matching 책임이므로 이동하지 않았고, `router_tenant.py`도 수정하지 않았습니다.

## 변경 파일

- `backend/WEB_SERVER/routers/router_tenant_edi.py`

## 생성 파일

- `backend/WEB_SERVER/routers/router_tenant_edi_jobs.py`
- `backend/WEB_SERVER/routers/router_tenant_edi_exports.py`
- `mulAg/review/REVIEW-018.md`

## 미변경 파일

- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/app.py`
- `backend/WEB_SERVER/services/service_email.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`
- `backend/DATABASE`

## 라인 수

- `backend/WEB_SERVER/routers/router_tenant_edi.py`: 17 lines
- `backend/WEB_SERVER/routers/router_tenant_edi_jobs.py`: 225 lines
- `backend/WEB_SERVER/routers/router_tenant_edi_exports.py`: 244 lines

## 검증 내용

- `ReadAllLines` 기준 모든 EDI 관련 라우터 파일이 300라인 이하임을 확인했습니다.
- `compile()` 기반 문법 확인 통과:
  - `backend/WEB_SERVER/routers/router_tenant_edi.py`
  - `backend/WEB_SERVER/routers/router_tenant_edi_jobs.py`
  - `backend/WEB_SERVER/routers/router_tenant_edi_exports.py`

## 남은 이슈

- TODO-018 범위 내 남은 이슈는 없습니다.
- 전체 tenant 라우터의 mapping/verification 분리는 TODO-004, TODO-005 후속 범위로 남습니다.

## QA 확인 요청 사항

- `router_tenant_edi.py`가 aggregator로만 동작하며 `/api/tenant` prefix를 중복하지 않는지 확인해 주세요.
- EDI jobs/export 하위 라우터가 모두 300라인 이하인지 확인해 주세요.
- `request_match_attempt`가 이동되지 않았고 matching 책임이 유지되는지 확인해 주세요.
