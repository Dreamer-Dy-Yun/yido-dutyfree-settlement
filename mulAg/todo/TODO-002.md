# TODO: router_tenant 사용자/사용량/테넌트 정보 라우트 분리

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- `router_tenant.py`에서 사용자 관리/테넌트 사용량/테넌트 정보 API를 분리해 `router_tenant_users.py`로 이관한다.

## 작업 범위

- 분리 대상 endpoint:
  - `GET /api/tenant/users`
  - `POST /api/tenant/users`
  - `GET /api/tenant/users/{user_id}`
  - `PUT /api/tenant/users/{user_id}`
  - `PATCH /api/tenant/users/{user_id}/activation`
  - `DELETE /api/tenant/users/{user_id}`
  - `POST /api/tenant/users/{user_id}/reset-password`
  - `GET /api/tenant/usage`
  - `GET /api/tenant/usage/users/{user_id}/tokens`
  - `GET /api/tenant/info`
  - `PUT /api/tenant/info`
- 기존 라우터의 공용 헬퍼 함수 중 사용자 도메인에서 참조되는 최소 집합만 별도 모듈로 정리.

## 선행 조건

- TODO-001 완료 후 app 라우터 등록 실책이 최소화된 상태.

## 수정 가능 파일

- `backend/WEB_SERVER/routers/router_tenant.py`

## 생성 가능 파일

- `backend/WEB_SERVER/routers/router_tenant_users.py`
- `mulAg/review/REVIEW-002.md`

## 읽기 전용 파일

- `backend/WEB_SERVER/routers/tenant_helpers.py`
- `backend/WEB_SERVER/services/auth_service.py`
- `backend/WEB_SERVER/services/auth_service.py`
- `backend/WEB_SERVER/routers/tenant_schemas.py`

## 수정 금지 파일

- `backend/PROCESSOR_MATCHING`
- `backend/PROCESSOR_DATA`
- `DATABASE/models/tenant_model.py`
- `backend/WEB_SERVER/app.py`

## 입력

- 소스 라우터: `backend/WEB_SERVER/routers/router_tenant.py`
- 사용자/사용량 엔드포인트 라인: 453, 1799, 1875, 1909, 1959, 1998, 2064, 2115, 2751, 2813, 2826
- 공통 권한/DB 종속성 패턴: `Depends(...)`

## 출력

- `backend/WEB_SERVER/routers/router_tenant_users.py`
- `backend/WEB_SERVER/routers/router_tenant.py`(이관 후 라우트만 제거)

## 작업 단계

- [ ] 1. `backend/WEB_SERVER/routers/router_tenant_users.py` 생성 및 엔드포인트 이관.
- [ ] 2. 필요한 Pydantic 스키마/유틸 임포트 정리.
- [ ] 3. `router_tenant.py`에서 해당 라우트 함수 제거.
- [ ] 4. `router_tenant.py` aggregator에서 신규 라우터 include 등록.
- [ ] 5. 공통 헬퍼가 이동되었는지 라우트/임포트 경로 점검.

## 완료 기준

- 대상 11개 엔드포인트가 `router_tenant_users.py`로만 노출됨.
- `router_tenant.py`는 사용자·사용량·테넌트정보 라우트 중복 정의 없음.
- `backend/WEB_SERVER/app.py` 변경 없이 기존 `/api/tenant` prefix가 유지됨.
- 기존 라우팅 동작 변화 없이 라우트 목록에서 404/409 변경 없음(문서 기준 검증).

## 주의사항

- 사용자/비밀번호 변경 API에서 실패 메시지와 상태코드가 기존 스펙과 다르면 안 됨.
- `get_current_user` 기반 인증 흐름은 유지한다.
- 하위 라우터에는 `/api/tenant` prefix를 중복 지정하지 않는다.
