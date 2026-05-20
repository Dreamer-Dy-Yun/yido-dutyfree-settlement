# TODO: router_tenant_edi 300라인 초과 해소

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- TODO-003 결과물인 `router_tenant_edi.py`가 300라인을 초과한 문제를 해소한다.

## 작업 범위

- EDI upload/job 실행 라우트와 EDI export/list/detail 라우트를 파일 단위로 분리한다.
- `router_tenant_edi.py`는 aggregator로 축소하거나 가장 작은 책임만 유지한다.

## 선행 조건

- TODO-003 review 보류 상태

## 수정 가능 파일

- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/routers/router_tenant_edi.py`

## 생성 가능 파일

- `backend/WEB_SERVER/routers/router_tenant_edi_jobs.py`
- `backend/WEB_SERVER/routers/router_tenant_edi_exports.py`
- `mulAg/review/REVIEW-018.md`

## 읽기 전용 파일

- `mulAg/review/REVIEW-003.md`
- `backend/WEB_SERVER/routers/tenant_helpers.py`
- `backend/WEB_SERVER/routers/tenant_schemas.py`

## 수정 금지 파일

- `backend/WEB_SERVER/app.py`
- `backend/WEB_SERVER/services/service_email.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`
- `backend/DATABASE`

## 입력

- `router_tenant_edi.py`의 upload/job/export/groups/detail 라우트
- QA 예상 보류 사유: 신규 파일 300라인 초과

## 출력

- 300라인 이하의 EDI 관련 라우터 파일들
- `router_tenant.py`의 기존 `/api/tenant` aggregator 경로 유지
- `REVIEW-018.md`

## 작업 단계

- [ ] 1. upload/job/run/status 라우트를 `router_tenant_edi_jobs.py`로 이동한다.
- [ ] 2. excel export/groups/detail 라우트를 `router_tenant_edi_exports.py`로 이동한다.
- [ ] 3. `router_tenant_edi.py`는 하위 라우터 include 또는 최소 책임 파일로 정리한다.
- [ ] 4. 관련 파일 ReadAllLines 기준 라인 수와 문법 검증 결과를 review에 기록한다.

## 완료 기준

- EDI 관련 라우터 파일이 모두 300라인 이하.
- `/api/tenant` prefix 중복 없음.
- `app.py` 변경 없음.
- TODO-003 보류 사유가 해소됨.

## 주의사항

- `request_match_attempt`는 matching 책임이므로 이번 작업에 포함하지 않는다.
