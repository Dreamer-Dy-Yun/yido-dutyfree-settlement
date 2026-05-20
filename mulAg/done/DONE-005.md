# REVIEW: TODO-005 matching/verification mutation route split

## 수행 일시

2026-05-20 15:16:09

## 참조 plan

mulAg/plan/active/PLAN-20260520-backend-cleanup.md

## 참조한 todo

mulAg/todo/TODO-005.md

## 수행 내용

- `router_tenant.py`를 `/api/tenant` prefix aggregator로 유지했습니다.
- `router_tenant_matching.py`를 생성하고 matching 라우트와 영수증/여권 검수 mutation 라우트를 이동했습니다.
- 하위 라우터에는 `/api/tenant` prefix를 중복 지정하지 않고 `APIRouter()`만 사용했습니다.
- `router_tenant.py`에서 `tenant_matching_router`를 include하도록 연결했습니다.
- TODO-004 범위였던 이미지/OCR 하위 라우터 파일은 수정하지 않았습니다.

## 이동한 라우트

- `POST /data-mapping/match-attempt`
- `POST /internal/match/run`
- `GET /data-mapping/match-status`
- `GET /data-mapping/matches`
- `GET /data-mapping/matches/{uuid_receipt}`
- `POST /data-mapping/receipts/verify`
- `DELETE /data-mapping/receipts/verify`
- `POST /data-mapping/receipts/bulk-verify`
- `POST /data-mapping/passports/verify`
- `DELETE /data-mapping/passports/verify`
- `POST /data-mapping/passports/bulk-verify`

## 변경 파일

- `backend/WEB_SERVER/routers/router_tenant.py`

## 생성 파일

- `backend/WEB_SERVER/routers/router_tenant_matching.py`
- `mulAg/review/REVIEW-005.md`

## 미변경 파일

- `backend/WEB_SERVER/app.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`
- `backend/WEB_SERVER/services/service_email.py`
- `backend/DATABASE`
- `backend/WEB_SERVER/routers/router_tenant_image.py`

## 라인 수

- `backend/WEB_SERVER/routers/router_tenant.py`: 296 lines
- `backend/WEB_SERVER/routers/router_tenant_matching.py`: 943 lines

## 검증 내용

- `py -3 -m py_compile backend/WEB_SERVER/routers/router_tenant.py backend/WEB_SERVER/routers/router_tenant_matching.py` 통과.
- `router_tenant.py`에 `/api/tenant` prefix가 유지되고, `router_tenant_matching.py`는 `APIRouter()`만 사용하는 것을 확인했습니다.
- `py_compile`로 생성된 `__pycache__` 부산물은 작업 범위 밖 파일로 남기지 않기 위해 제거했습니다.

## 남은 이슈

- `router_tenant_matching.py`는 ReadAllLines 기준 943라인으로 300라인 기준을 초과합니다.
- 이번 TODO의 생성 가능 파일이 `router_tenant_matching.py` 하나로 제한되어 matching 조회, matching 실행, 영수증 검수, 여권 검수를 추가 파일로 분리하지 못했습니다.
- 후속 TODO에서 `router_tenant_matching_jobs.py`, `router_tenant_matching_queries.py`, `router_tenant_receipt_verification.py`, `router_tenant_passport_verification.py`처럼 책임별로 나누는 것이 필요합니다.

## QA 확인 요청 사항

- 이동한 라우트가 `/api/tenant` prefix 아래에서 기존 path/method를 유지하는지 확인해 주세요.
- `router_tenant_matching.py` 300라인 초과를 이번 TODO의 제한 조건상 보류 이슈로 인정할지, 후속 TODO로 반려할지 판단해 주세요.
