# TODO: router_tenant 매칭/검증 라우트 분리

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- `router_tenant.py`의 매칭 실행, 상태 조회, 수동 매칭/검증/삭제 API를 `router_tenant_matching.py`로 분리한다.

## 작업 범위

- 분리 대상 endpoint:
  - `GET /api/tenant/data-mapping/match-status`
  - `POST /api/tenant/internal/match/run`
  - `GET /api/tenant/data-mapping/matches`
  - `GET /api/tenant/data-mapping/matches/{match_id}`
  - `GET /api/tenant/data-mapping/receipts-for-review`
  - `GET /api/tenant/data-mapping/passports-for-review`
  - `POST /api/tenant/data-mapping/verify-receipt`
  - `DELETE /api/tenant/data-mapping/receipts/{receipt_uuid}`
  - `POST /api/tenant/data-mapping/verify-passport`
  - `DELETE /api/tenant/data-mapping/passports/{passport_uuid}`
  - `POST /api/tenant/data-mapping/bulk-verify-receipts`
  - `POST /api/tenant/data-mapping/bulk-verify-passports`

## 선행 조건

- TODO-003 또는 TODO-004와 endpoint 겹침이 없도록 사전 정리.

## 수정 가능 파일

- `backend/WEB_SERVER/routers/router_tenant.py`

## 생성 가능 파일

- `backend/WEB_SERVER/routers/router_tenant_matching.py`
- `mulAg/review/REVIEW-005.md`

## 읽기 전용 파일

- `backend/WEB_SERVER/services/service_match_queue.py`
- `backend/PROCESSOR_MATCHING`
- `backend/WEB_SERVER/routers/tenant_helpers.py`
- `backend/WEB_SERVER/routers/tenant_schemas.py`

## 수정 금지 파일

- `backend/WEB_SERVER/services/service_email.py`
- `backend/DATABASE/models`
- `backend/DATABASE/dbms`
- `backend/WEB_SERVER/app.py`

## 입력

- 소스 라우터 라인 지점: 932-974, 1105-1149, 1183-1399, 1512-1518, 1628, 2161-2167, 2277-2540, 2592-2598
- 라우트 핸들러 이름:
  - internal_run_match_job
  - get_match_status
  - list_matches
  - get_match_detail
  - list_receipts_for_review
  - list_passports_for_review
  - verify_receipt
  - delete_receipt
  - verify_passport
  - delete_passport
  - bulk_verify_receipts
  - bulk_verify_passports

## 출력

- `backend/WEB_SERVER/routers/router_tenant_matching.py`
- `backend/WEB_SERVER/routers/router_tenant.py`(이관 후 중복 라우트 삭제)

## 작업 단계

- [ ] 1. 매칭/검증 핸들러와 헬퍼를 신규 라우터로 이동.
- [ ] 2. 요청/응답 타입, 의존성, 인증 데코레이션 유지.
- [ ] 3. 원본 라우터 import 및 helper 사용부 충돌 정리.
- [ ] 4. `router_tenant.py` aggregator 라우터 등록 추가 및 라우트 목록 점검.

## 완료 기준

- 목록에 있는 11개 핸들러만 신규 라우터로 이동.
- 라우트 실패/성공 응답 구조는 기존과 동일.
- 기존 코드와 신규 라우터 간의 순환 import 없음.
- `backend/WEB_SERVER/app.py` 변경 없이 기존 `/api/tenant` prefix가 유지됨.

## 주의사항

- 배치 bulk verify 경로에서 트랜잭션 에러가 감추어지지 않도록 기존 예외 전파 정책 유지.
- 하위 라우터에는 `/api/tenant` prefix를 중복 지정하지 않는다.
