# REVIEW: router_system_admin 계정/키/프롬프트 라우트 분리

## 수행 일시

2026-05-20 14:48:45

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 참조한 todo

- TODO-007.md

## 수행 내용

- `router_system_admin.py`를 `/api/system-admin` aggregator로 유지했습니다.
- service-accounts 라우트 5개를 `router_system_admin_service_accounts.py`로 이동했습니다.
- llm-api-keys 라우트 5개를 `router_system_admin_llm_api_keys.py`로 이동했습니다.
- prompts 라우트 5개를 `router_system_admin_prompts.py`로 이동했습니다.
- `app.py` 변경 없이 기존 `router_system_admin` include 경로를 유지했습니다.
- LLM API Key 응답은 helper를 거쳐 `api_key`를 마스킹하도록 했습니다.
- service account 응답은 helper를 거쳐 `password`를 제거하도록 했습니다.

## 변경 파일

- `backend/WEB_SERVER/routers/router_system_admin.py`

## 생성 파일

- `backend/WEB_SERVER/routers/router_system_admin_service_accounts.py`
- `backend/WEB_SERVER/routers/router_system_admin_llm_api_keys.py`
- `backend/WEB_SERVER/routers/router_system_admin_prompts.py`
- `mulAg/review/REVIEW-007.md`

## 미변경 파일

- `backend/WEB_SERVER/app.py`
- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/services/service_email.py`
- `backend/DATABASE`

## 검증 내용

- ReadAllLines 기준 라인 수를 확인했습니다.
  - `router_system_admin.py`: 24 lines
  - `router_system_admin_service_accounts.py`: 256 lines
  - `router_system_admin_llm_api_keys.py`: 175 lines
  - `router_system_admin_prompts.py`: 176 lines
- `compile()` 기반 문법 확인을 통과했습니다.
- 테스트/빌드 실행은 수행하지 않았습니다.

## 남은 이슈

- `router_system_admin_service_accounts.py`의 DB 삭제는 기존 구현의 raw SQL 삭제 방식을 유지했습니다.
- LLM API Key 생성/수정 응답도 raw key를 반환하지 않도록 기존보다 엄격하게 마스킹했습니다.

## QA 확인 요청 사항

- 총 15개 라우트가 세 하위 라우터로 이동되었는지 확인 바랍니다.
- `router_system_admin.py`가 aggregator로만 남고 `app.py` 변경 없이 동작하는지 확인 바랍니다.
- 신규 파일이 모두 300라인 이하인지 확인 바랍니다.
