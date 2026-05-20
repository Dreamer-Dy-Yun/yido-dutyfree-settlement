# TODO: router_tenant 이미지/OCR 라우트 분리

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- `router_tenant.py`에서 이미지 업로드/상태 조회/이미지 매핑 조회 API를 `router_tenant_image.py`로 분리한다.

## 작업 범위

- 분리 대상 endpoint:
  - `POST /api/tenant/data-mapping/image-upload`
  - `GET /api/tenant/data-mapping/image-ocr-progress`
  - `GET /api/tenant/data-mapping/image/{hash_img}`
  - `GET /api/tenant/data-mapping/image-details`

## 선행 조건

- TODO-002 또는 TODO-003와 충돌하지 않도록 대상 엔드포인트 확정.

## 수정 가능 파일

- `backend/WEB_SERVER/routers/router_tenant.py`

## 생성 가능 파일

- `backend/WEB_SERVER/routers/router_tenant_image.py`
- `mulAg/review/REVIEW-004.md`

## 읽기 전용 파일

- `backend/WEB_SERVER/services/service_image_ocr.py`
- `backend/WEB_SERVER/routers/tenant_helpers.py`
- `backend/WEB_SERVER/routers/tenant_schemas.py`

## 수정 금지 파일

- `backend/PROCESSOR_MATCHING`
- `backend/PROCESSOR_DATA`
- `backend/DATABASE/models`
- `backend/WEB_SERVER/app.py`

## 입력

- 소스 라우터 라인 지점: 968, 1110-1149, 1622, 1679, 1685
- 라우트 핸들러 이름: upload_image_zip, get_image_ocr_progress, get_data_mapping_image, get_data_mapping_details_by_image

## 출력

- `backend/WEB_SERVER/routers/router_tenant_image.py`
- `backend/WEB_SERVER/routers/router_tenant.py`(이관 후 해당 라우트 제거)

## 작업 단계

- [ ] 1. 이미지/OCR 라우트와 관련 응답 스키마/도메인 헬퍼만 추출.
- [ ] 2. 신규 라우터에 prefix, tags, 오류 데코레이터 일관성 유지.
- [ ] 3. 원본 라우터에서 라우트 함수 제거 및 중복 import 정리.
- [ ] 4. `router_tenant.py` aggregator에서 신규 라우터 등록.

## 완료 기준

- 위 endpoint가 `router_tenant_image.py`로 이동.
- OCR 진행 조회와 상세 조회 응답 형태 보존.
- 원본 라우터에서 라우트 중복 정의 없음.
- `backend/WEB_SERVER/app.py` 변경 없이 기존 `/api/tenant` prefix가 유지됨.

## 주의사항

- 파일/이미지 path를 처리하는 로직에서 상대경로 계산 규칙은 유지.
- 이미지 조회 권한(테넌트 스키마/유저 인증)은 기존 동작과 동일.
- 하위 라우터에는 `/api/tenant` prefix를 중복 지정하지 않는다.
