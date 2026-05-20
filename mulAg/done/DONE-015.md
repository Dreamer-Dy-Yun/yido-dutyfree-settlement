# REVIEW: service_email 회사 거부/삭제 템플릿 분리

## 수행 일시

2026-05-20 14:42:17

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 참조한 todo

- TODO-015.md

## 수행 내용

- `EmailService.set_company_rejection_email`의 HTML/text MIME 생성 책임을 `build_company_rejection_email` builder로 분리했다.
- `EmailService.set_company_deletion_email`의 HTML/text MIME 생성 책임을 `build_company_deletion_email` builder로 분리했다.
- `EmailService`의 공개 메서드 시그니처, `Self` 체이닝 반환, `send()` 위치를 유지했다.
- `email_company_templates.py`는 기존 회사 등록/승인 builder와 신규 거부/삭제 builder를 모두 담되, 공통 page/card/message helper를 사용해 ReadAllLines 기준 300라인 이하로 정리했다.

## 변경 파일

- `backend/WEB_SERVER/services/service_email.py`
- `backend/WEB_SERVER/services/email_company_templates.py`

## 생성 파일

- `mulAg/review/REVIEW-015.md`

## 미변경 파일

- `backend/WEB_SERVER/routers`
- `backend/WEB_SERVER/app.py`
- `backend/DATABASE`
- 테스트 파일

## 라인 수

- `backend/WEB_SERVER/services/service_email.py`: 259 lines
- `backend/WEB_SERVER/services/email_company_templates.py`: 231 lines

## 검증 내용

- `service_email.py`, `email_company_templates.py`를 `compile()`로 문법 확인했고 모두 통과했다.
- `py_compile`은 `__pycache__` 생성을 피하기 위해 사용하지 않았다.

## 남은 이슈

- `email_company_templates.py`의 기존 회사 등록/승인 subject 문자열은 이전 상태의 호환성을 유지하기 위해 이번 TODO에서 별도 수정하지 않았다.
- SMTP transport 분리와 DB account resolver 분리는 TODO-015 범위 밖이다.
- 최초 TODO-015 문서에는 `email_company_templates.py`가 수정 가능 파일로 명시되지 않았다. Orchestrator가 QA 보류 후 TODO-015 권한 범위를 실제 회사 템플릿 파일 기준으로 보정했다.

## QA 확인 요청 사항

- TODO-015의 수정 가능 파일 범위 준수 여부를 확인해 달라.
- 회사 거부/삭제 메서드의 공개 API와 체이닝 반환 유지 여부를 확인해 달라.
- ReadAllLines 기준 300라인 제한 충족 여부를 확인해 달라.
