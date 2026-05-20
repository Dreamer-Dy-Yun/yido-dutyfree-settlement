# REVIEW: tenant image router split

## 수행 일시

2026-05-20 15:12:11

## 참조 plan

mulAg/plan/active/PLAN-20260520-backend-cleanup.md

## 참조한 todo

mulAg/todo/TODO-004.md

## 수행 내용

- `router_tenant.py`는 `/api/tenant` prefix를 가진 aggregator로 유지했습니다.
- 이미지 ZIP 업로드, OCR 진행률, 이미지 파일 반환, 이미지 상세 조회 라우트를 `router_tenant_image.py`로 이동했습니다.
- 하위 라우터는 `APIRouter()`만 사용하고 `/api/tenant` prefix를 중복 지정하지 않았습니다.
- matching/list/verify mutation 라우트는 TODO-005 또는 후속 범위로 남겼습니다.
- `app.py`, `router_system_admin.py`, `service_email.py`, `DATABASE`는 수정하지 않았습니다.

## 변경 파일

- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant.py
  - `tenant_image_router` import 및 include 추가
  - 이미지/OCR 전용 라우트 4개 제거
  - ReadAllLines 기준 1193라인

## 생성 파일

- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant_image.py
  - 이미지 ZIP 업로드, OCR 진행률, 이미지 파일 반환, 이미지 상세 조회 라우트 보관
  - ReadAllLines 기준 300라인
- D:\DEV\YIDO\mulAg\review\REVIEW-004.md

## 미변경 파일

- D:\DEV\YIDO\backend\WEB_SERVER\app.py
- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_system_admin.py
- D:\DEV\YIDO\backend\WEB_SERVER\services\service_email.py
- D:\DEV\YIDO\backend\DATABASE

## 검증 내용

- `compile()`로 `router_tenant.py`, `router_tenant_image.py` 문법 확인 통과.
- `router_tenant_image.py` 신규 파일은 ReadAllLines 기준 300라인으로 기준을 충족.
- `rg`로 `image-upload`, `image-ocr-progress`, `data-mapping/image/{hash_img}`, `image-details` 라우트가 `router_tenant_image.py`에만 있는 것을 확인.
- `router_tenant.py`에서 `tenant_image_router` import 및 include를 확인.

## 남은 이슈

- `router_tenant.py`는 matching/list/verify mutation이 남아 1193라인입니다. 이는 TODO-005 또는 후속 범위입니다.
- `router_tenant_image.py`가 정확히 300라인이므로, 이미지 라우터에 기능을 추가할 때는 하위 파일 분리가 먼저 필요합니다.
- 원본의 깨진 OpenAPI summary/description 문자열은 새 파일로 그대로 복사하지 않고 데코레이터를 축소했습니다. path/method와 반환 필드 구조는 유지했습니다.

## QA 확인 요청 사항

- `router_tenant.py` aggregator 유지와 `/api/tenant` prefix 중복 없음 확인.
- 이미지/OCR 범위만 이동했고 matching/list/verify mutation이 남아 있는지 확인.
- 신규 파일 300라인 기준과 금지 파일 미수정 여부 확인.
