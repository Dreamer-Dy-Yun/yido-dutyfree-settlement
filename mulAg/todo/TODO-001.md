# TODO: router_registration 라우트 등록 정리

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- `backend/WEB_SERVER/routers/router_registration.py`에 있는 회원가입 라우트를 FastAPI 앱에 실제 등록한다.
- 라우트 누락으로 인한 API 공백을 제거한다.

## 작업 범위

- `backend/WEB_SERVER/app.py`의 라우터 import/include 블록 정리.
- 필요한 경우 라우터 등록 순서를 유지한다.

## 선행 조건

- 없음

## 수정 가능 파일

- `backend/WEB_SERVER/app.py`

## 생성 가능 파일

- 없음

## 읽기 전용 파일

- `backend/WEB_SERVER/routers/router_registration.py`
- `backend/WEB_SERVER/routers/router_auth.py`
- `backend/WEB_SERVER/routers/router_company.py`
- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`

## 수정 금지 파일

- `frontend`
- `infra`
- `DATABASE`
- 기존 테스트 파일 일괄 삭제/이동

## 입력

- 등록 대상 라우터: `router_registration.router`
- 라우터 prefix: `/api/registration`
- 현재 앱 등록 패턴: `app.include_router(...)`

## 출력

- `backend/WEB_SERVER/app.py`
- `mulAg/review/TODO-001-review-*.md` (예정)

## 작업 단계

- [ ] 1. `backend/WEB_SERVER/app.py`에서 `router_registration` import 추가.
- [ ] 2. `app.include_router(router_registration)` 등록.
- [ ] 3. 등록 위치와 기존 라우터 등록 순서 문서화.
- [ ] 4. 변경 근거를 `review` 초안에 기록.

## 완료 기준

- `/api/registration/register` 및 `/api/registration/verify-email` 경로가 `router` 등록 리스트에 포함됨.
- 기존 라우트 동작이 기존 상태에서 제거되지 않음.
- 변경 파일이 TODO에서 지정한 범위만 반영됨.

## 주의사항

- route prefix/태그/의존성 동작은 수정하지 않는다.
- 기능 삭제 또는 임의 성공 응답 추가는 금지한다.

