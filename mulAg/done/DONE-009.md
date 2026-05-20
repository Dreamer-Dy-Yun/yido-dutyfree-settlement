# REVIEW: 경계 문서/README 동기화

## 수행 일시

2026-05-20 14:20:00

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 참조한 todo

- TODO-009.md

## 수행 내용

- `backend/WEB_SERVER/routers/README.md`를 현재 라우터 aggregator/sub-router 구조에 맞게 갱신했습니다.
- `backend/WEB_SERVER/services/README.md`를 현재 email facade/template 분리 구조에 맞게 갱신했습니다.
- `MD/MODULE_BOUNDARIES.md`의 split candidates와 known open issues를 현재 완료/잔여 상태 기준으로 갱신했습니다.

## 변경 파일

- `MD/MODULE_BOUNDARIES.md`
- `backend/WEB_SERVER/routers/README.md`
- `backend/WEB_SERVER/services/README.md`

## 생성 파일

- `mulAg/review/REVIEW-009.md`

## 미변경 파일

- `backend/WEB_SERVER/app.py`
- `backend/WEB_SERVER/routers/*.py`
- `backend/WEB_SERVER/services/*.py`

## 검증 내용

- 문서에 `router_registration.py` 등록 상태를 반영했습니다.
- `router_tenant.py`, `router_system_admin.py`가 aggregator라는 현재 구조를 문서화했습니다.
- `service_email.py`는 template split 완료, transport/account resolver 잔여로 문서화했습니다.
- `registration_service.py` 설명을 등록된 `/api/registration` 라우터 기준으로 보정했습니다.
- `test_backend_contract_hardening.py`를 services README 파일 목록에 추가했습니다.

## 남은 이슈

- mojibake 문구 정리는 기능/구조 정리와 분리된 별도 TODO가 필요합니다.
- SMTP transport와 DB account resolver 분리는 후속 서비스 hardening TODO가 필요합니다.

## QA 확인 요청 사항

- 문서가 현재 파일 구조와 맞는지 확인 요청.
- plan 완료 판단에 필요한 문서 동기화 기준 충족 여부 확인 요청.
