# REVIEW: router_registration 라우트 등록 정리

## 수행 일시

2026-05-20 13:45:00

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 참조한 todo

- TODO-001.md

## 수행 내용

- `backend/WEB_SERVER/app.py`에 `/api/registration` 라우트를 제공하는 `router_registration` 모듈을 FastAPI 앱에 등록했습니다.
- `router_auth`와 동일한 import 그룹에 `router_registration`을 추가했습니다.
- 기존 회사 라우트 등록 뒤에 `app.include_router(router_registration)`을 추가해 라우트 노출 순서를 유지했습니다.

## 변경 파일

- `backend/WEB_SERVER/app.py`

## 생성 파일

- 없음

## 미변경 파일

- `backend/WEB_SERVER/routers/router_registration.py`
- `backend/WEB_SERVER/routers/router_auth.py`
- `backend/WEB_SERVER/routers/router_company.py`
- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`
- `mulAg/todo/TODO-001.md`
- `mulAg/plan/active/PLAN-20260520-backend-cleanup.md`

## 검증 내용

- `git diff` 기준 변경사항으로 `backend/WEB_SERVER/app.py`에 import/route include가 각각 1건씩 추가됨을 확인.
- 파일 인코딩 점검에서 `backend/WEB_SERVER/app.py`는 UTF-8 BOM 유지 상태였고, 변경 범위 외 문자열은 변경되지 않았음.

## 남은 이슈

- `backend/WEB_SERVER/app.py` 전체에서 기존 한국어 문자열이 일부 환경에서 깨져 보이는 현상이 관찰되어, 실제 기능 변경 없이 표시 레이어 인코딩 점검이 추가로 필요함.

## QA 확인 요청 사항

- `TODO-001` 완료 조건인 `/api/registration/register` 및 `/api/registration/verify-email` 라우트 등록 상태가 정상인지 QA 단계에서 확인 요청.
- 다른 라우터 등록 순서/권한 미변경 여부 확인 요청.
