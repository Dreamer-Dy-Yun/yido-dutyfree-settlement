# REVIEW: TODO-019 router_tenant_matching 추가 분리

## 수행 일시

2026-05-20 15:20:06

## 참조 plan

mulAg/plan/active/PLAN-20260520-backend-cleanup.md

## 참조한 todo

mulAg/todo/TODO-019.md

## 수행 내용

- `router_tenant_matching.py`를 matching 영역 aggregator로 축소했습니다.
- match request/internal run/status 라우트를 `router_tenant_match_jobs.py`로 분리했습니다.
- match list/detail 및 receipt/passport review list 라우트를 `router_tenant_match_results.py`로 분리했습니다.
- receipt/passport verification mutation 라우트를 `router_tenant_verification.py`로 분리했습니다.
- `router_tenant.py`는 `/api/tenant` prefix를 가진 최상위 aggregator 역할만 유지하도록 정리했습니다.
- 신규 하위 라우터는 모두 `APIRouter()`만 사용해 `/api/tenant` prefix를 중복하지 않았습니다.

## 변경 파일

- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant.py
- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant_matching.py

## 생성 파일

- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant_match_jobs.py
- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant_match_results.py
- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant_verification.py
- D:\DEV\YIDO\mulAg\review\REVIEW-019.md

## 라인 수

- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant.py: 21 lines
- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant_matching.py: 19 lines
- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant_match_jobs.py: 104 lines
- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant_match_results.py: 283 lines
- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant_verification.py: 292 lines

## 미변경 파일

- D:\DEV\YIDO\backend\WEB_SERVER\app.py
- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_tenant_image.py
- D:\DEV\YIDO\backend\WEB_SERVER\routers\router_system_admin.py
- D:\DEV\YIDO\backend\WEB_SERVER\services\service_email.py
- D:\DEV\YIDO\backend\DATABASE

## 검증 내용

- `py -3 -m py_compile backend\WEB_SERVER\routers\router_tenant.py backend\WEB_SERVER\routers\router_tenant_matching.py backend\WEB_SERVER\routers\router_tenant_match_jobs.py backend\WEB_SERVER\routers\router_tenant_match_results.py backend\WEB_SERVER\routers\router_tenant_verification.py` 통과.
- `ReadAllLines` 기준 모든 대상 파일이 300라인 이하임을 확인했습니다.
- `py_compile`로 생성될 수 있는 대상 라우터 pyc 캐시 파일은 작업 산출물에서 제외되도록 제거했습니다.

## 남은 이슈

- 전체 API 동작 테스트나 백엔드 통합 테스트는 실행하지 않았습니다.
- verification 라우트는 라인 수 기준을 맞추기 위해 일부 중복을 공통 helper로 접었지만, DB 트랜잭션 경계 자체는 기존 구현 흐름을 유지했습니다.

## QA 확인 요청 사항

- TODO-019 허용 파일 범위 위반 여부 확인.
- `/api/tenant` prefix 중복이 없는지 확인.
- matching job/result/review list/verification mutation 라우트가 중복 등록 없이 유지되는지 확인.
- 모든 변경/생성 Python 파일이 300라인 이하인지 확인.
