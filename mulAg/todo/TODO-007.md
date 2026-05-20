# TODO: router_system_admin 계정/키/프롬프트 라우트 분리

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- `router_system_admin.py` aggregator를 유지하면서 service-accounts, llm-api-keys, prompts 도메인을 하위 라우터로 분리한다.

## 작업 범위

- 분리 대상 endpoint:
  - service-accounts:
    - `GET /api/system-admin/service-accounts`
    - `GET /api/system-admin/service-accounts/{account_id}`
    - `POST /api/system-admin/service-accounts`
    - `PUT /api/system-admin/service-accounts/{account_id}`
    - `DELETE /api/system-admin/service-accounts/{account_id}`
  - llm-api-keys:
    - `GET /api/system-admin/llm-api-keys`
    - `GET /api/system-admin/llm-api-keys/{api_key_id}`
    - `POST /api/system-admin/llm-api-keys`
    - `PUT /api/system-admin/llm-api-keys/{api_key_id}`
    - `DELETE /api/system-admin/llm-api-keys/{api_key_id}`
  - prompts:
    - `GET /api/system-admin/prompts`
    - `GET /api/system-admin/prompts/{prompt_id}`
    - `POST /api/system-admin/prompts`
    - `PUT /api/system-admin/prompts/{prompt_id}`
    - `DELETE /api/system-admin/prompts/{prompt_id}`

## 선행 조건

- TODO-006 완료

## 수정 가능 파일

- `backend/WEB_SERVER/routers/router_system_admin.py`

## 생성 가능 파일

- `backend/WEB_SERVER/routers/router_system_admin_service_accounts.py`
- `backend/WEB_SERVER/routers/router_system_admin_llm_api_keys.py`
- `backend/WEB_SERVER/routers/router_system_admin_prompts.py`
- `mulAg/review/REVIEW-007.md`

## 읽기 전용 파일

- `backend/WEB_SERVER/routers/tenant_schemas.py`
- `backend/WEB_SERVER/services/service_email.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`

## 수정 금지 파일

- `backend/DATABASE/models`
- `backend/PROCESSOR_MATCHING`
- `backend/WEB_SERVER/app.py`

## 입력

- 라인 범위:
  - service-accounts: 586-812
  - llm-api-keys: 848-965
  - prompts: 986-1104
- 라우트 함수명:
  - get_service_accounts, get_service_account_detail, create_service_account, update_service_account, delete_service_account
  - get_llm_api_keys, get_llm_api_key_detail, create_llm_api_key, update_llm_api_key, delete_llm_api_key
  - get_prompts, get_prompt_detail, create_prompt, update_prompt, delete_prompt

## 출력

- `backend/WEB_SERVER/routers/router_system_admin_service_accounts.py`
- `backend/WEB_SERVER/routers/router_system_admin_llm_api_keys.py`
- `backend/WEB_SERVER/routers/router_system_admin_prompts.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`(이관 후 라우트 제거)

## 작업 단계

- [ ] 1. service-account 라우트 이관.
- [ ] 2. llm-key 라우트 이관.
- [ ] 3. prompt 라우트 이관.
- [ ] 4. 기존 라우터에서 라우트 제거 및 중복 import 정리.
- [ ] 5. 기존 `router_system_admin.py` aggregator에 하위 라우터 include 등록.

## 완료 기준

- 총 15개 라우트가 전용 라우터로 이전.
- 라우트 별 응답 스키마와 상태코드 보존.
- `backend/WEB_SERVER/app.py` 변경 없이 기존 `router_system_admin` include 경로가 유지됨.

## 주의사항

- `llm-api-key` 마스킹 정책은 신규 라우터에서도 동일하게 유지.
- 관리자권한 요구 조건은 라우터 전환으로 변경되지 않아야 함.
