# TODO: router_tenant_matching 300라인 초과 해소

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- TODO-005 결과물인 `router_tenant_matching.py`가 300라인을 크게 초과한 문제를 해소한다.

## 작업 범위

- matching job/status/list/detail 라우트와 receipt/passport verification mutation 라우트를 파일 단위로 분리한다.
- `router_tenant_matching.py`는 aggregator로 축소한다.

## 선행 조건

- TODO-005 review 보류 상태

## 수정 가능 파일

- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/routers/router_tenant_matching.py`

## 생성 가능 파일

- `backend/WEB_SERVER/routers/router_tenant_match_jobs.py`
- `backend/WEB_SERVER/routers/router_tenant_match_results.py`
- `backend/WEB_SERVER/routers/router_tenant_verification.py`
- `mulAg/review/REVIEW-019.md`

## 읽기 전용 파일

- `mulAg/review/REVIEW-005.md`
- `backend/WEB_SERVER/routers/tenant_helpers.py`
- `backend/WEB_SERVER/routers/tenant_schemas.py`

## 수정 금지 파일

- `backend/WEB_SERVER/app.py`
- `backend/WEB_SERVER/routers/router_tenant_image.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`
- `backend/WEB_SERVER/services/service_email.py`
- `backend/DATABASE`

## 입력

- `router_tenant_matching.py`의 matching job/status/list/detail 라우트
- `router_tenant_matching.py`의 receipt/passport verification mutation 라우트
- QA 예상 보류 사유: 신규 파일 300라인 초과

## 출력

- 300라인 이하의 matching 관련 라우터 파일들
- `router_tenant.py`의 기존 `/api/tenant` aggregator 경로 유지
- `REVIEW-019.md`

## 작업 단계

- [ ] 1. match request/internal run/status 라우트를 `router_tenant_match_jobs.py`로 이동한다.
- [ ] 2. match list/detail/review list 라우트를 `router_tenant_match_results.py`로 이동한다.
- [ ] 3. receipt/passport verify/delete/bulk 라우트를 `router_tenant_verification.py`로 이동한다.
- [ ] 4. `router_tenant_matching.py`는 하위 라우터 include 역할로 축소한다.
- [ ] 5. 관련 파일 ReadAllLines 기준 라인 수와 문법 검증 결과를 review에 기록한다.

## 완료 기준

- matching/verification 관련 라우터 파일이 모두 300라인 이하.
- `/api/tenant` prefix 중복 없음.
- `app.py` 변경 없음.
- TODO-005 보류 사유가 해소됨.

## 주의사항

- 이미지/OCR 라우터와 EDI 라우터는 수정하지 않는다.
- 검수 helper의 동작과 DB mutation 순서는 변경하지 않는다.
