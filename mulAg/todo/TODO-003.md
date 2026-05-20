# TODO: router_tenant EDI 라우트 분리

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- `router_tenant.py`에서 EDI 업로드/통합/조회/내보내기 관련 라우트를 분리해 `router_tenant_edi.py`로 추출한다.

## 작업 범위

- 분리 대상 endpoint:
  - `POST /api/tenant/data-mapping/edi-upload`
  - `POST /api/tenant/data-mapping/edi-unified-run`
  - `GET /api/tenant/data-mapping/edi-unified-job/{job_id}`
  - `POST /api/tenant/internal/edi-unified/run`
  - `GET /api/tenant/data-mapping/edi-unified-excel`
  - `GET /api/tenant/data-mapping/edi-unified-groups`
  - `GET /api/tenant/data-mapping/edi-unified-group/{edi_unified_group_id}`

## 선행 조건

- TODO-002 완료 또는 라우트 이관 기준이 `router_tenant.py` aggregator에 반영된 상태.

## 수정 가능 파일

- `backend/WEB_SERVER/routers/router_tenant.py`

## 생성 가능 파일

- `backend/WEB_SERVER/routers/router_tenant_edi.py`
- `mulAg/review/REVIEW-003.md`

## 읽기 전용 파일

- `backend/WEB_SERVER/routers/tenant_helpers.py`
- `backend/WEB_SERVER/services/service_edi_unified_queue.py`
- `backend/PROCESSOR_DATA`
- `backend/WEB_SERVER/routers/tenant_schemas.py`

## 수정 금지 파일

- `backend/WEB_SERVER/services/service_email.py`
- `backend/DATABASE`
- `backend/WEB_SERVER/app.py`

## 입력

- 소스 라우터 라인 지점: 492, 603, 609, 644-704, 699, 704, 777, 882, 884
- 라우트 핸들러 이름: upload_edi_data, request_edi_unified_run, get_edi_unified_job, internal_run_edi_unified_job, export_edi_unified_excel, list_edi_unified_groups, get_edi_unified_group_detail

## 출력

- `backend/WEB_SERVER/routers/router_tenant_edi.py`
- `backend/WEB_SERVER/routers/router_tenant.py`(이관 후 해당 라우트 제거)

## 작업 단계

- [ ] 1. EDI endpoint 관련 핸들러만 추출.
- [ ] 2. 신규 라우터 파일에 동일 prefix 및 태그를 유지.
- [ ] 3. 기존 라우터의 해당 라우트 삭제 후 의존성 정리.
- [ ] 4. `router_tenant.py` aggregator에서 라우트 등록 순서 정합성 확인.

## 완료 기준

- 위 7개 endpoint가 `router_tenant_edi.py` 계열 라우터에서만 정의.
- `/api/tenant/internal/edi-unified/run`의 인증/권한 조건 유지.
- `backend/WEB_SERVER/app.py` 변경 없이 기존 `/api/tenant` prefix가 유지됨.
- 분리 후 라우트 임포트 누락이 없어 빌드 단계 import 오류 없음.

## 주의사항

- 내부용 엔드포인트(`/internal/...`)는 사용자용 라우터와 같은 prefix에서 분리되어도 보안 의존성은 동일해야 함.
- 템플릿/엑셀 파일 처리 경로는 기존 상대경로 규칙 유지.
- 하위 라우터에는 `/api/tenant` prefix를 중복 지정하지 않는다.
- `request_match_attempt`는 matching 책임이므로 EDI 라우터로 이동하지 않는다.
